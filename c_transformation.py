import os
import re
from io import BytesIO
from pathlib import Path
import subprocess
from lxml import etree
import config
from utils import filehelper
from utils import shellhelper


def get_methods_of_file(file_path: str):
    xml_name = filehelper.generate_random_file_name_with_extension('xml')
    methods = []
    try:
        shellhelper.run("cgum '{}' > {}".format(file_path, xml_name))
        xml_p = Path(xml_name)
        xml_bytes = xml_p.read_bytes()
        methods = get_methods_of_xml_bytes(xml_bytes)
    finally:
        xml_p.unlink()
        return methods


def get_methods_of_xml_bytes(xml_bytes):
    if xml_bytes is not None:
        xml_object = etree.parse(BytesIO(xml_bytes))
        methods = xml_object.xpath('//tree[@typeLabel="Definition"]/tree[@typeLabel="Definition"]')
        return methods
    else:
        return []


def generate_c_file_of_blob(file_blob):
    java_name = filehelper.generate_random_file_name_with_extension('c')
    java_p = Path(java_name)
    java_p.write_bytes(file_blob.data_stream.read())
    return str(java_p.resolve())


def get_method_signature(method_xml):
    method_xml = sanitize(method_xml)
    name_xpath = '//tree[@typeLabel="Definition"]/tree[@typeLabel="GenericString"]'
    parameters_xpath = '//tree[@typeLabel="Definition"]/tree[@typeLabel="ParamList"]/' \
                       'tree[@typeLabel="ParameterType"]/tree[@typeLabel="GenericString"]/@label'
    parameters_element = method_xml.xpath(name_xpath)
    if parameters_element is not None and len(parameters_element) > 0:
        method_name_str = parameters_element[0].get("label")
        parameters = method_xml.xpath(parameters_xpath)
        parameters_str = '(' + ','.join(map(str, parameters)) + ')'
        return method_name_str, parameters_str
    else:
        return '', ''


def compare_method_signature(method_xml_a, method_xml_b):
    a_method_signature = get_method_signature(method_xml_a)
    b_method_signature = get_method_signature(method_xml_b)
    is_same_name = True if a_method_signature[0] == b_method_signature[0] else False
    is_same_parameters = True if a_method_signature[1] == b_method_signature[1] else False
    return is_same_name, is_same_parameters


def get_method_full_signature(method_xml):
    signature = get_method_signature(method_xml)
    return signature[0] + signature[1]


def get_logging_calls_xml_of_method(method_xml):
    result = []
    method_xml = sanitize(method_xml)
    method_calls_xml = get_method_calls(method_xml)
    for method_call_xml in method_calls_xml:
        if _is_logging_call(method_call_xml):
            result.append(method_call_xml)
    return result


def get_method_calls(method_xml):
    # TODO: Get first call directly
    method_xml = sanitize(method_xml)
    xpath_str = '//tree[@typeLabel="FunCall"]'
    method_calls_xml = method_xml.xpath(xpath_str)
    return method_calls_xml


def _is_logging_call(method_call_xml):
    # Work on this case later
    # if is_argument_none(method_call_xml):
    #     return False
    method_call_xml = sanitize(method_call_xml)
    method_call_name = get_method_call_name(method_call_xml)
    if method_call_name in config.uniq_log_fun:
        #print(method_call_name)
        return True
    return False


def get_method_call_name(method_call_xml):
    method_call_xml = sanitize(method_call_xml)
    call_xpath_str = '//tree[@typeLabel="FunCall"]/tree[@typeLabel="Ident"]/tree[@typeLabel="GenericString"]'
    call_xpath_str_2 = '//tree[@typeLabel="FunCall"]/tree[@typeLabel="RecordPtAccess"]/tree[@typeLabel="GenericString"]'
    method_call_name = method_call_xml.xpath(call_xpath_str)
    if len(method_call_name) == 0:
        method_call_name = method_call_xml.xpath(call_xpath_str_2)
    if method_call_name:
        return method_call_name[0].get("label")
    else:
        return ""


def sanitize(xml):
    return etree.fromstring(etree.tostring(xml).decode(encoding='utf-8'))


def get_string_xml(root, file):
    start = int(root.get("line_before"))
    end = int(root.get("line_after"))
    str_root = " ".join(line for line in file[start-1:end])
    return str_root


def get_string_xml_strip(root, file):
    start = int(root.get("line_before"))
    end = int(root.get("line_after"))
    str_root = " ".join(line.rstrip() for line in file[start-1:end])
    return str_root


def get_string_xml_vars(root, file):
    start = int(root.get("line_before"))
    end = int(root.get("line_after"))
    c_start = int(root.get("col_before"))
    c_end = int(root.get("col_after"))
    result = ""
    if start != end:
        i = start - 1
        for line in file[start-1:end]:
            if i == start-1:
                result += line[c_start:].rstrip().lstrip()
            elif i == end-1:
                result += line[:c_end].rstrip().lstrip()
            else:
                result += line.rstrip().lstrip()
            i = i + 1
        return result
    else:
        str_root = " ".join(line for line in file[start - 1:end])
        return str_root[c_start:c_end].rstrip().lstrip()


def get_all_vars(call, file):
    call = sanitize(call)
    # print("jfjksdfjksd")
    # print(etree.tostring(call).decode(encoding='utf-8'))
    vars_xpath = '/tree[@typeLabel="FunCall"]/tree[@typeLabel="GenericList"]/tree[@typeLabel="Left"]'
    text_xpath = '/tree[@typeLabel="Left"]/tree[@typeLabel="Constant"]'
    sim_xpath = '/tree[@typeLabel="Left"]/tree[@typeLabel="FunCall"]'
    all_vars = call.xpath(vars_xpath)
    result = []
    for var in all_vars:
        if not sanitize(var).xpath(sim_xpath):
            if not sanitize(var).xpath(text_xpath):
                result.append(str(get_string_xml_vars(var, file).encode(), encoding='unicode_escape'))

    return result


def get_string_vars(call):
    call = sanitize(call)
    text_xpath = '/tree[@typeLabel="FunCall"]/tree[@typeLabel="GenericList"]/' \
                 'tree[@typeLabel="Left"]/tree[@typeLabel="Constant"]'
    result = []

    texts = call.xpath(text_xpath)
    for text in texts:
        result.append(str(text.get("label").encode(), encoding='unicode_escape'))

    return result


def get_sim_vars(call):
    call = sanitize(call)
    sim_xpath = '/tree[@typeLabel="FunCall"]/tree[@typeLabel="GenericList"]' \
                '/tree[@typeLabel="Left"]/tree[@typeLabel="FunCall"]'

    sims = call.xpath(sim_xpath)

    result = []
    for sim in sims:
        result.append(str(get_method_call_name(sim).encode(), encoding='unicode_escape'))
        sims_in_sim = get_sim_vars(sim)
        for m in sims_in_sim:
            result.append(m)

    return result

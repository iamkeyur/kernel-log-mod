#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from pathlib import Path
import subprocess
from lxml import etree
import config
from utils import filehelper
from utils import shellhelper


ns = {"src": "http://www.srcML.org/srcML/src"}


def get_xml_bytes_of_c(file_blob):
    fifo_name = filehelper.generate_random_file_name_with_extension('c')
    os.mkfifo(fifo_name)

    try:
        process = subprocess.Popen(['srcml', fifo_name], stdout=subprocess.PIPE)
        with open(fifo_name, 'wb') as f:
            f.write(file_blob.data_stream.read())
        output = process.stdout.read()
    finally:
        os.remove(fifo_name)
    return output


def generate_c_file_of_blob(file_blob):
    java_name = filehelper.generate_random_file_name_with_extension('c')
    java_p = Path(java_name)
    java_p.write_bytes(file_blob.data_stream.read())
    return str(java_p.resolve())


def get_methods_of_file(file_path: str):
    xml_name = filehelper.generate_random_file_name_with_extension('xml')
    os.system("cgum '{}' > '{}'".format(file_path, xml_name))
    with open(xml_name) as f:
        xml = f.read()
    parser = etree.XMLParser(encoding='utf-8')
    xml_object = etree.parse(xml_name, parser=parser)
    methods = xml_object.xpath('//src:unit/src:function', namespaces=ns)
    #os.remove(xml_name)
    return methods

    # methods = []
    # try:
    #     process = subprocess.Popen("srcml '{}'".format(file_path), shell=True, stdout=subprocess.PIPE)
    #     #shellhelper.run("srcml '{}' -o {}".format(file_path, xml_name))
    #     (output, err) = process.communicate()
    #     #print(output.decode('utf-8'))
    #     # xml_p = Path(xml_name)
    #     # xml_bytes = xml_p.read_bytes()
    #     methods = get_methods_of_xml_bytes(output)
    # finally:
    #     pass
    #     # xml_p.unlink()
    #     return methods


def get_methods_of_c_blob(file_blob):
    xml_bytes = get_xml_bytes_of_c(file_blob)
    methods = get_methods_of_xml_bytes(xml_bytes)
    return methods


def get_methods_of_xml_bytes(xml_bytes):
    if xml_bytes is not None:
        parser = etree.XMLParser(huge_tree=True)
        xml_object = etree.fromstring(xml_bytes, parser=parser)
        methods = xml_object.xpath('//src:unit/src:function', namespaces=ns)
        return methods
    else:
        return []


def transform_xml_str_to_code(xml_str):
    xml_str = xml_str.split('>', 1)[-1]
    xml_str = xml_str[:-7]
    pre_str = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><unit xmlns="http://www.srcML.org/srcML/src" xmlns:cpp="http://www.srcML.org/srcML/cpp" revision="0.9.5" language="C" filename="x.c"><macro>'
    xml_str = pre_str + xml_str + '</macro></unit>'
    print(xml_str)
    fifo_name = filehelper.generate_random_file_name_with_extension('xml')
    os.mkfifo(fifo_name)

    try:
        process = subprocess.Popen(['srcml', fifo_name], stdout=subprocess.PIPE)
        with open(fifo_name, 'w') as f:
            f.write(xml_str)
        output = process.stdout.read()
    finally:
        os.remove(fifo_name)
    return str(output.decode(encoding='utf-8'))


def generate_c_file_of_str(text: str):
    java_name = filehelper.generate_random_file_name_with_extension('c')
    java_p = Path(java_name)
    java_p.open('w').write(text)
    return str(java_p.resolve())


def transform_log_str_to_xml_obj(code_str):
    # print("from here")
    # print(code_str)
    # code_str_components = code_str.split('(', 1)
    # caller_method = code_str_components[0]
    # caller_method = caller_method.replace('\\n', '').replace('\\t', '').replace('\\r', '')
    # formatted_code_str = caller_method + '(' + code_str_components[1]

    java_file_path = generate_c_file_of_str(code_str + ";")
    xml_name = filehelper.generate_random_file_name_with_extension('xml')
    methods = []
    try:
        shellhelper.run("srcml '{}' -o {}".format(java_file_path, xml_name))
        xml_p = Path(xml_name)
        xml_bytes = xml_p.read_bytes()
        parser = etree.XMLParser(huge_tree=True)
        xml_object = etree.fromstring(xml_bytes, parser=parser)
        methods = get_method_calls(xml_object)

    finally:
        xml_p.unlink()
        java_p = Path(java_file_path)
        java_p.unlink()
        if len(methods) > 0:
            return methods[0]
        else:
            return None


def get_logging_calls_xml_of_repo(repo_path: str):
    java_file_list = filehelper.get_all_java_files(repo_path)
    result = []
    for java_path in java_file_list:
        logging_calls = get_logging_calls_xml_of_file(str(java_path))
        for call in logging_calls:
            result.append(call)

    return result


def get_logging_calls_xml_of_file(file_path: str):
    methods = get_methods_of_file(file_path)
    result = []
    for method in methods:
        method_str = b'<root>' + etree.tostring(method) + b'</root>'
        method = etree.fromstring(method_str)
        logging_calls = get_logging_calls_xml_of_method(method)
        for call in logging_calls:
            result.append(call)

    return result


def get_logging_calls_xml_of_method(method_xml):
    result = []
    method_calls_xml = get_method_calls(method_xml)
    for method_call_xml in method_calls_xml:
        if _is_logging_call(method_call_xml):
            result.append(method_call_xml)
    return result


def get_method_calls(method_xml):
    # TODO: Get first call directly
    xpath_str = '//src:expr_stmt/src:expr/*[1]'
    method_calls_xml = method_xml.xpath(xpath_str, namespaces=ns)
    result_method_calls_xml = method_calls_xml
    for item in method_calls_xml:
        #print(etree.tostring(item))
        if not etree.tostring(item).decode('utf-8').startswith('<call'):
            result_method_calls_xml.remove(item)
    return result_method_calls_xml


def _is_logging_call(method_call_xml):
    if is_argument_none(method_call_xml):
        return False

    method_call_name = get_method_call_name(method_call_xml)

    # level_name = None
    # if '.' in method_call_name:
    #     caller_name = method_call_name.rsplit('.', 1)[:-1][0]
    #     level_name = method_call_name.rsplit('.', 1)[-1:][0]
    # else:
    #     caller_name = method_call_name
    #
    # filter_caller_regex = '.*?(log|(system\.out)|(system\.err)|timber).*'
    # p = re.compile(filter_caller_regex, re.I)
    # m = p.match(caller_name)
    # if m is None:
    #     return False
    #
    # filter_caller_black_regex = '.*?(dialog|login|logout|loggedin|loggedout|catalog|logical|blog|logo).*'
    # p = re.compile(filter_caller_black_regex, re.I)
    # m = p.match(caller_name)
    # if m is not None:
    #     return False
    #
    # if level_name is not None:
    #     filter_level_white_regex = '^(w|e|v|i|d|wtf|warn|warning|error|verbose|info|debug|severe|fine|fatal|trace|print|printf|println|log)$'
    #     p = re.compile(filter_level_white_regex, re.I)
    #     m = p.match(level_name)
    #     if m is None:
    #         return False
    if method_call_name not in config.uniq_log_fun:
        return False

    return True


def is_argument_none(method_xml):
    arguments_xpath = './src:argument_list/src:argument'
    arguments = method_xml.xpath(arguments_xpath, namespaces=ns)
    if len(arguments) == 0:
        return True
    else:
        return False


def get_method_call_name(method_call_xml):
    method_call_name = ''
    call_with_operator_xpath_str = 'src:name//*'
    call_without_operator_xpath_str = 'src:name'
    method_call_name_xml = method_call_xml.xpath(call_with_operator_xpath_str, namespaces=ns)
    if len(method_call_name_xml) == 0:
        method_call_name_xml = method_call_xml.xpath(call_without_operator_xpath_str, namespaces=ns)
    for item in method_call_name_xml:
        if item.text is not None:
            method_call_name += item.text
    return method_call_name


def get_method_block_content(method_xml):
    content_xpath = '//src:function/src:block'
    content_xml = method_xml.xpath(content_xpath, namespaces=ns)[0]
    return content_xml


def get_logging_argument(method_xml):
    argument_xpath = './src:argument_list/src:argument'
    arguments = method_xml.xpath(argument_xpath, namespaces=ns)

    text_xpath = './src:expr/src:literal'
    var_xpath = './src:expr/src:name'
    sim_xpath = './src:expr/src:call'

    result = []

    if len(arguments) == 0:
        result.append(([], [], []))

    for index in range(0, len(arguments)):
        argument = arguments[index]
        text = argument.xpath(text_xpath, namespaces=ns)
        var = argument.xpath(var_xpath, namespaces=ns)
        sim = argument.xpath(sim_xpath, namespaces=ns)
        result.append((text, var, sim))

    return result


def get_all_var_str_in_call(method_xml):
    argument_xpath = './src:argument_list/src:argument'
    arguments = method_xml.xpath(argument_xpath, namespaces=ns)
    var_xpath = './src:expr/src:name'
    sim_xpath = './src:expr/src:call'

    result = []
    for index in range(0, len(arguments)):
        argument = arguments[index]
        variables = argument.xpath(var_xpath, namespaces=ns)
        sims = argument.xpath(sim_xpath, namespaces=ns)
        for var in variables:
            text = var.text
            if text is None:
                text = get_flattern_text(var)
            result.append(text)
        for sim in sims:
            sim_name = get_method_call_name(sim)
            if '.' in sim_name:
                caller_name = sim_name.rsplit('.', 1)[:-1][0]
            else:
                caller_name = sim_name
            result.append(caller_name)
            vars_in_sim = get_all_var_str_in_call(sim)
            for var in vars_in_sim:
                result.append(var)

    return result


def get_all_text_str_in_call(method_xml):
    argument_xpath = './src:argument_list/src:argument'
    arguments = method_xml.xpath(argument_xpath, namespaces=ns)
    text_xpath = './src:expr/src:literal'

    result = []
    for index in range(0, len(arguments)):
        argument = arguments[index]
        texts = argument.xpath(text_xpath, namespaces=ns)
        for text in texts:
            result.append(text.text)

    return result


def get_all_sim_str_in_call(method_xml):
    argument_xpath = './src:argument_list/src:argument'
    arguments = method_xml.xpath(argument_xpath, namespaces=ns)
    sim_xpath = './src:expr/src:call'

    result = []
    for index in range(0, len(arguments)):
        argument = arguments[index]
        sims = argument.xpath(sim_xpath, namespaces=ns)

        for sim in sims:
            sim_name = get_method_call_name(sim)
            result.append(sim_name)
            sims_in_sim = get_all_sim_str_in_call(sim)
            for method in sims_in_sim:
                result.append(method)

    return result


def get_method_signature(method_xml):
    name_xpath = '//src:function/src:name'
    # parameters_xpath = '//src:function/src:parameter_list/src:parameter/src:decl/src:type/src:name'
    parameters_xpath = '//src:function/src:parameter_list/src:parameter'
    parameters_element = method_xml.xpath(name_xpath, namespaces=ns)
    if parameters_element is not None and len(parameters_element) > 0:
        method_name = parameters_element[0]
        method_name_str = method_name.text
        parameters = method_xml.xpath(parameters_xpath, namespaces=ns)
        parameters_str = get_flatten_text_of_parameter(parameters)
        parameters_str = parameters_str[0:-1]
        parameters_str = '(' + parameters_str + ')'

        return method_name_str, parameters_str
    else:
        return '', ''


def get_method_full_signature(method_xml):
    signature = get_method_signature(method_xml)
    return signature[0] + signature[1]


def get_flattern_text(xml):
    result = ''
    if not isinstance(xml, list):
        if len(xml) == 0:
            result = result + xml.text
        else:
            for item in xml:
                result = result + get_flattern_text(item)
    else:
        for item in xml:
            result = result + get_flattern_text(item)
    return result


def get_flatten_text_of_parameter(xml):
    result = ''
    if not isinstance(xml, list):
        if len(xml) == 0:
            result = result + xml.text + ','
        else:
            for item in xml:
                result = result + get_flatten_text_of_parameter(item)
    else:
        for item in xml:
            result = result + get_flatten_text_of_parameter(item)
    return result


def compare_method_signature(method_xml_a, method_xml_b):
    a_method_signature = get_method_signature(method_xml_a)
    b_method_signature = get_method_signature(method_xml_b)
    is_same_name = True if a_method_signature[0] == b_method_signature[0] else False
    is_same_parameters = True if a_method_signature[1] == b_method_signature[1] else False
    return is_same_name, is_same_parameters

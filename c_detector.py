import logging
import codecs
from datetime import datetime
import Levenshtein
import re
from lxml import etree
import c_transformation
from utils import filehelper, githelper
import config
import getloc
import unicodedata
import c_metrics
from models import LogChangeType, Log

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


def diff_inspector(git_repo, commit_diff, head_commit_db):
    for file_diff in commit_diff:
        if file_diff.change_type == 'A':
            try:
                handle_added_file(file_diff, head_commit_db)
            except:
                pass
        elif file_diff.change_type == 'D':
            try:
                handle_deleted_file(file_diff, head_commit_db)
            except:
                pass
        elif file_diff.change_type == 'M' or \
                (file_diff.change_type.startswith('R') and file_diff.a_blob != file_diff.b_blob):
            try:
                handle_updated_file(file_diff, head_commit_db)
            except:
                pass


def update_log_loc(component, added, deleted, modified):
    if component == "core":
        config.core_add += added
        config.core_del += deleted
        config.core_mod += modified
    if component == "fs":
        config.fs_add += added
        config.fs_del += deleted
        config.fs_mod += modified
    if component == "driver":
        config.driver_add += added
        config.driver_del += deleted
        config.driver_mod += modified
    if component == "net":
        config.net_add += added
        config.net_del += deleted
        config.net_mod += modified
    if component == "arch":
        config.arch_add += added
        config.arch_del += deleted
        config.arch_mod += modified
    if component == "misc":
        config.misc_add += added
        config.misc_del += deleted
        config.misc_mod += modified
    if component == "firmware":
        config.firmware_add += added
        config.firmware_del += deleted
        config.firmware_mod += modified


def print_stats():
    print("core")
    print("added " + str(config.core_add))
    print("deleted " + str(config.core_del))
    print("mod " + str(config.core_mod))

    print("fs")
    print("added " + str(config.fs_add))
    print("deleted " + str(config.fs_del))
    print("mod " + str(config.fs_mod))

    print("driver")
    print("added " + str(config.driver_add))
    print("deleted " + str(config.driver_del))
    print("mod " + str(config.driver_mod))

    print("net")
    print("added " + str(config.net_add))
    print("deleted " + str(config.net_del))
    print("mod " + str(config.net_mod))

    print("arch")
    print("added " + str(config.arch_add))
    print("deleted " + str(config.arch_del))
    print("mod " + str(config.arch_mod))

    print("misc")
    print("added " + str(config.misc_add))
    print("deleted " + str(config.misc_del))
    print("mod " + str(config.misc_mod))

    print("firmware")
    print("added " + str(config.firmware_add))
    print("deleted " + str(config.firmware_del))
    print("mod " + str(config.firmware_mod))


def get_component(filepath):
    core_files = ["init", "block", "ipc", "kernel", "lib", "mm", "virt"]
    fs_files = ["fs"]
    driver_files = ["crypto", "drivers", "sound", "security"]
    net_files = ["net"]
    arch_files = ["arch"]
    misc_files = ["Documentation", "scripts", "samples", "usr", "MAINTAINERS", "CREDITS", "README",
                  ".gitignore", "Kbuild", "Makefile", "REPORTING-BUGS", ".mailmap", "COPYING", "tools",
                  "Kconfig", "LICENSES", "certs", ".clang-format"]
    firmware_files = ["firmware"]

    folder = filepath.split("/")[0]

    if folder in core_files:
        return "core"
    if folder in fs_files:
        return "fs"
    if folder in driver_files:
        return "driver"
    if folder in net_files:
        return "net"
    if folder in arch_files:
        return "arch"
    if folder in misc_files:
        return "misc"
    if folder in firmware_files:
        return "firmware"

    return ""


def handle_added_file(file_diff, head_commit_db):
    logging_loc, component = handle_added_or_deleted_file(file_diff.b_path, file_diff.b_blob,
                                                          LogChangeType.ADDED_WITH_FILE, head_commit_db)
    update_log_loc(component, logging_loc, 0, 0)


def handle_deleted_file(file_diff, head_commit_db):
    logging_loc, component = handle_added_or_deleted_file(file_diff.a_path, file_diff.a_blob,
                                                          LogChangeType.DELETED_WITH_FILE, head_commit_db)
    update_log_loc(component, 0, logging_loc, 0)


def handle_added_or_deleted_file(file_path, file_blob, change_type, head_commit_db):
    file_logging_loc = 0
    component = get_component(file_path)
    if filehelper.is_c_file(file_path):
        c_file = c_transformation.generate_c_file_of_blob(file_blob)

        with codecs.open(c_file, 'r', encoding='utf-8',
                         errors='ignore') as f:
            src = f.readlines()
            f.close()

        methods = c_transformation.get_methods_of_file(c_file)

        for method in methods:
            log_loc = save_logs_of_method_xml_str_if_needed(change_type, file_path, head_commit_db,
                                                            method, component, src)
            file_logging_loc += log_loc
        filehelper.delete_if_exists(c_file)
    return file_logging_loc, component


def handle_updated_file(file_diff, head_commit_db):
    if filehelper.is_c_file(file_diff.a_path) and filehelper.is_c_file(file_diff.b_path):
        component = get_component(file_diff.b_path)
        c_a_file = c_transformation.generate_c_file_of_blob(file_diff.a_blob)
        c_b_file = c_transformation.generate_c_file_of_blob(file_diff.b_blob)

        with codecs.open(c_a_file, 'r', encoding='utf-8',
                         errors='ignore') as f:
            src = f.readlines()
            f.close()

        with codecs.open(c_b_file, 'r', encoding='utf-8',
                         errors='ignore') as f:
            dst = f.readlines()
            f.close()

        methods_parent = c_transformation.get_methods_of_file(c_a_file)
        methods_head = c_transformation.get_methods_of_file(c_b_file)

        file_added_logging_loc, file_deleted_logging_loc, file_updated_logging_loc = \
            compare_all_methods(methods_parent, methods_head, src, dst, file_diff, head_commit_db, component)
        filehelper.delete_if_exists(c_a_file)
        filehelper.delete_if_exists(c_b_file)
        update_log_loc(component, file_added_logging_loc, file_deleted_logging_loc, file_updated_logging_loc)


def remove_hash(xml_str):
    return str(xml_str.split('#', 1)[1])


def helper(x, f):
    b = etree.fromstring(remove_hash(x))
    return str(c_transformation.get_string_xml_vars(b, f).encode(), encoding='unicode_escape')


def compare_logging_method_calls(head_commit_db, file_diff, method_name, logging_method_calls_in_parent,
                                 logging_method_calls_in_head, src, dst, component):
    method_mapping_list = []
    method_added_logging_loc = 0
    method_deleted_logging_loc = 0
    method_updated_logging_loc = 0

    # Add index to make each call unique.
    method_calls_str_parent = \
        [str(index) + '#' + etree.tostring(call).decode('utf-8') for index, call in
         enumerate(logging_method_calls_in_parent)]
    method_calls_str_head = \
        [str(index) + '#' + etree.tostring(call).decode('utf-8') for index, call in
         enumerate(logging_method_calls_in_head)]

    for call_str_in_parent in method_calls_str_parent:
        for call_str_in_head in method_calls_str_head:
            distance_ratio = Levenshtein.ratio(
                c_transformation.get_string_xml_vars(etree.fromstring(remove_hash(call_str_in_parent)), src),
                c_transformation.get_string_xml_vars(etree.fromstring(remove_hash(call_str_in_head)), dst))
            if distance_ratio > config.LEVENSHTEIN_RATIO_THRESHOLD:
                is_parent_in_mapping = False
                # Check mapping list
                for mapping in method_mapping_list:
                    call_mapping_parent = mapping[0]
                    mapping_ratio = mapping[2]
                    if call_str_in_parent == call_mapping_parent:
                        is_parent_in_mapping = True
                        if distance_ratio > mapping_ratio:
                            mapping[1] = call_str_in_head
                            mapping[2] = Levenshtein.ratio(
                                c_transformation.get_string_xml_vars(etree.fromstring(remove_hash(call_str_in_parent)), src),
                                c_transformation.get_string_xml_vars(etree.fromstring(remove_hash(call_str_in_head)), dst))
                if not is_parent_in_mapping:
                    is_head_in_mapping = False
                    for mapping in method_mapping_list:
                        call_mapping_head = mapping[1]
                        mapping_ratio = mapping[2]
                        if call_str_in_head == call_mapping_head:
                            is_head_in_mapping = True
                            if distance_ratio > mapping_ratio:
                                mapping[0] = call_str_in_parent
                                mapping[2] = Levenshtein.ratio(
                                    c_transformation.get_string_xml_vars(etree.fromstring(remove_hash(call_str_in_parent)),
                                                                    src),
                                    c_transformation.get_string_xml_vars(etree.fromstring(remove_hash(call_str_in_head)),
                                                                dst))
                    if not is_head_in_mapping:
                        method_mapping_list.append([str(call_str_in_parent), str(call_str_in_head), distance_ratio])

    method_calls_mapping_in_parent = []
    method_calls_mapping_in_head = []
    for mapping in method_mapping_list:
        change_from = etree.fromstring(remove_hash(mapping[0]))
        change_to = etree.fromstring(remove_hash(mapping[1]))
        method_calls_mapping_in_parent.append(
            str(c_transformation.get_string_xml_vars(change_from, src).encode(), encoding='unicode_escape'))
        method_calls_mapping_in_head.append(
            str(c_transformation.get_string_xml_vars(change_to, dst).encode(), encoding='unicode_escape'))

    before = []
    after = []
    for m in method_calls_str_parent:
        b = etree.fromstring(remove_hash(m))
        before.append(str(c_transformation.get_string_xml_vars(b, src).encode(), encoding='unicode_escape'))

    for m in method_calls_str_head:
        a = etree.fromstring(remove_hash(m))
        after.append(str(c_transformation.get_string_xml_vars(a, dst).encode(), encoding='unicode_escape'))

    deleted_logging_calls_str = list(set(before) - set(method_calls_mapping_in_parent))
    added_logging_calls_str = list(set(after) - set(method_calls_mapping_in_head))

    if added_logging_calls_str or deleted_logging_calls_str:
        print("Added Calls : ")
        print(added_logging_calls_str)
        print("Deleted Calls :")
        print(deleted_logging_calls_str)

    method_deleted_logging_loc += len(deleted_logging_calls_str)
    method_added_logging_loc += len(added_logging_calls_str)

    for call_str in deleted_logging_calls_str:
        save_logs_of_logging_call_xml(call_str, LogChangeType.DELETED_INSIDE_METHOD, file_diff.a_path,
                                      head_commit_db, method_name, component)

    for call_str in added_logging_calls_str:
        save_logs_of_logging_call_xml(call_str, LogChangeType.ADDED_INSIDE_METHOD, file_diff.b_path, head_commit_db,
                                      method_name, component)
    for mapping in method_mapping_list:
        change_from = etree.fromstring(remove_hash(mapping[0]))
        change_to = etree.fromstring(remove_hash(mapping[1]))

        if c_transformation.get_string_xml_vars(change_from, src) != c_transformation.get_string_xml_vars(change_to, dst):
            print("Change from : ")
            print(c_transformation.get_string_xml_vars(change_from, src))
            print("Change to : ")
            print(c_transformation.get_string_xml_vars(change_to, dst))
            update_type = None
            method_updated_logging_loc += 1
            log = Log.create(commit_id=head_commit_db.hexsha, file_path=file_diff.b_path, embed_method=method_name,
                             change_type=LogChangeType.UPDATED,
                             content_update_from=c_transformation.get_string_xml_vars(change_from, src),
                             content_update_to=c_transformation.get_string_xml_vars(change_to, dst),
                             update_type=update_type, component=component)
            log.update_type = c_metrics.get_log_update_detail(change_from, change_to, src, dst)
            print(log.update_type)
            old_caller_object = c_transformation.get_method_call_name(change_from)
            new_caller_object = c_transformation.get_method_call_name(change_to)

            verb = re.compile(
                "KERN_EMERG|KERN_ALERT|KERN_CRIT|KERN_ERR|KERN_WARNING|KERN_NOTICE|KERN_INFO|KERN_DEBUG|KERN_CONT")

            if old_caller_object != new_caller_object:
                log.old_log_method = old_caller_object
                log.new_log_method = new_caller_object
            else:
                old_match = re.search(verb, c_transformation.get_string_xml_vars(change_from, src))
                new_match = re.search(verb, c_transformation.get_string_xml_vars(change_to, dst))
                if old_match and new_match:
                    if old_match.group(0) != new_match.group(0):
                        log.old_verb = old_match.group(0)
                        log.new_verb = new_match.group(0)
                else:
                    if old_match or new_match:
                        if old_match:
                            log.old_verb = old_match.group(0)
                        if new_match:
                            log.new_verb = new_match.group(0)
            log.save()

    return method_added_logging_loc, method_deleted_logging_loc, method_updated_logging_loc


def compare_all_methods(methods_parent, methods_head, src, dst, file_diff, head_commit_db, component):
    file_added_logging_loc = 0
    file_deleted_logging_loc = 0
    file_updated_logging_loc = 0

    method_parent_strings = [c_transformation.get_string_xml_strip(method, src) for method in methods_parent]
    method_head_strings = [c_transformation.get_string_xml_strip(method, dst) for method in methods_head]
    # Get idex of methods in parent and not in head
    idx_p = get_complement_of_a_in_b(method_head_strings, method_parent_strings)
    # Get idex of methods in head and not in parent
    idx_h = get_complement_of_a_in_b(method_parent_strings, method_head_strings)

    methods_only_in_parent = [methods_parent[i] for i in idx_p]
    methods_only_in_head = [methods_head[i] for i in idx_h]
    methods_xml_already_checked_in_parent = []
    methods_xml_already_checked_in_head = []

    # 1. Compare methods with same signature.
    for method_parent_xml in methods_only_in_parent:
        # method_parent_str = b'<root>' + method_parent_str + b'</root>'
        for method_head_xml in methods_only_in_head:
            # method_head_str = b'<root>' + method_head_str + b'</root>'
            if method_head_xml in methods_xml_already_checked_in_head:
                continue
            is_same_name, is_same_parameters = c_transformation.compare_method_signature(method_parent_xml,
                                                                                         method_head_xml)
            if is_same_name and is_same_parameters:
                # Methods with same signature, it is modified
                logging_method_calls_in_parent = c_transformation.get_logging_calls_xml_of_method(method_parent_xml)
                logging_method_calls_in_head = c_transformation.get_logging_calls_xml_of_method(method_head_xml)
                method_name = c_transformation.get_method_full_signature(method_head_xml)
                method_added_logging_loc, method_deleted_logging_loc, method_updated_logging_loc = \
                    compare_logging_method_calls(head_commit_db, file_diff, method_name,
                                                 logging_method_calls_in_parent, logging_method_calls_in_head, src, dst,
                                                 component)
                file_added_logging_loc += method_added_logging_loc
                file_deleted_logging_loc += method_deleted_logging_loc
                file_updated_logging_loc += method_updated_logging_loc
                methods_xml_already_checked_in_parent.append(method_parent_xml)
                methods_xml_already_checked_in_head.append(method_head_xml)
                break

    # 2. Compare rest methods with different signature
    for method_parent_xml in methods_only_in_parent:
        # method_parent_str = b'<root>' + method_parent_str + b'</root>'
        if method_parent_xml in methods_xml_already_checked_in_parent:
            continue
        for method_head_xml in methods_only_in_head:
            # method_head_str = b'<root>' + method_head_str + b'</root>'
            if method_head_xml in methods_xml_already_checked_in_head:
                continue
            is_same_name, is_same_parameters = c_transformation.compare_method_signature(method_parent_xml,
                                                                                         method_head_xml)
            block_content_str_in_parent = c_transformation.get_string_xml_strip(method_parent_xml, src)
            block_content_str_in_head = c_transformation.get_string_xml_strip(method_head_xml, dst)
            if is_same_name and not is_same_parameters:
                #  if method name are same, that is parameter declaration change.
                if block_content_str_in_parent == block_content_str_in_head:
                    # text are same, no need to compare
                    pass
                else:
                    # if text not same, method is modified, deal with the same process above.
                    logging_method_calls_in_parent = c_transformation.get_logging_calls_xml_of_method(method_parent_xml)
                    logging_method_calls_in_head = c_transformation.get_logging_calls_xml_of_method(method_head_xml)
                    method_name = c_transformation.get_method_full_signature(method_head_xml)
                    method_added_logging_loc, method_deleted_logging_loc, method_updated_logging_loc = \
                        compare_logging_method_calls(head_commit_db, file_diff, method_name,
                                                     logging_method_calls_in_parent, logging_method_calls_in_head, src,
                                                     dst,
                                                     component)
                    file_added_logging_loc += method_added_logging_loc
                    file_deleted_logging_loc += method_deleted_logging_loc
                    file_updated_logging_loc += method_updated_logging_loc
                methods_xml_already_checked_in_parent.append(method_parent_xml)
                methods_xml_already_checked_in_head.append(method_head_xml)
            elif not is_same_name and not is_same_parameters:
                if block_content_str_in_parent == block_content_str_in_head:
                    # if text are same, no log changed. They are renamed method.
                    methods_xml_already_checked_in_parent.append(method_parent_xml)
                    methods_xml_already_checked_in_head.append(method_head_xml)

    # 3. For the rest methods, they are added or deleted
    for method_parent_xml in methods_only_in_parent:
        # method_parent_str = b'<root>' + method_parent_str + b'</root>'
        if method_parent_xml not in methods_xml_already_checked_in_parent:
            # they are deleted, mark log calls in those methods as deleted.
            file_deleted_logging_loc += save_logs_of_method_xml_str_if_needed(LogChangeType.DELETED_WITH_METHOD,
                                                                              file_diff.a_path, head_commit_db,
                                                                              method_parent_xml, component, src)
    for method_head_xml in methods_only_in_head:
        # method_head_str = b'<root>' + method_head_str + b'</root>'
        if method_head_xml not in methods_xml_already_checked_in_head:
            # they are added, mark log calls in those methods as added.
            file_added_logging_loc += save_logs_of_method_xml_str_if_needed(LogChangeType.ADDED_WITH_METHOD,
                                                                            file_diff.b_path, head_commit_db,
                                                                            method_head_xml, component, dst)

    return file_added_logging_loc, file_deleted_logging_loc, file_updated_logging_loc


def save_logs_of_method_xml_str_if_needed(change_type, file_path, head_commit_db, method_xml, component, file):
    method_name = c_transformation.get_method_full_signature(method_xml)
    logging_calls = c_transformation.get_logging_calls_xml_of_method(method_xml)
    logging_calls_final = \
        [str(index) + '#' + etree.tostring(call).decode('utf-8') for index, call in
         enumerate(logging_calls)]
    for call_xml in logging_calls_final:
        save_logs_of_logging_call_xml(c_transformation.get_string_xml_vars(etree.fromstring(
            remove_hash(call_xml)), file), change_type, file_path, head_commit_db, method_name, component)
    return len(logging_calls)


def save_logs_of_logging_call_xml(call_str, change_type, file_path, head_commit_db, method_name, component):
    Log.create(commit_id=head_commit_db.hexsha, file_path=file_path, embed_method=method_name, change_type=change_type,
               content_update_to=call_str, component=component)


def get_complement_of_a_in_b(a_collection, b_collection):
    result = []
    for item in b_collection:
        if item not in a_collection:
            result.append(b_collection.index(item))
    return result


def detect_project(repo, need_pull: bool, until_date: datetime):
    # e54c78a27fcdef406af799f360a93e6754adeefe
    # 10004f813152646deeeb1e61a521b7ca026aa837
    # 83af41947c5cbdf33c78f4818bb0cb23da39d132
    # 7a5bd1279bce2116af67979bea311a0ccc4b8bb9
    # e13606d7321c0c08d4ac2d74a1102680a40cfdee
    # 101fa0371478aa0457c58e175b8f66a110c4b24c
    # 513770f54edba8b19c2175a151e02f1dfc911d87
    with open("cc", "r") as f:
        cc = f.readlines()
    for i in range(0, len(cc)):
        print("Now processing : " + str(cc[i]))
        print("\n")
        head_commit_sha = cc[i]
        head_commit = githelper.get_spec_commit(repo, head_commit_sha)
        if head_commit.parents:
            if len(head_commit.parents) > 1:
                is_merge_commit = True
            print("Len of parents is : " + str(len(head_commit.parents)) + "\n\n")
            for parent_commit in head_commit.parents:
                diff = githelper.get_diff_between_commits(parent_commit, head_commit)
                diff_inspector(repo, diff, head_commit)
                print("\n\n")
                print_stats()
            print("Done With One Commit! Hurray! i is: " + str(i) + "\n\n")

    # head_commit = githelper.get_spec_commit(repo, "bb2ab10fa693110cffa7087ffe2749d6e9a27d5f")
    # if head_commit.parents:
    #     if len(head_commit.parents) > 1:
    #         is_merge_commit = True
    #     print("Len of parents is : " + str(len(head_commit.parents)) + "\n\n")
    #     for parent_commit in head_commit.parents:
    #         parent_commit_sha = parent_commit.hexsha
    #         print("Now parent is  : " + str(parent_commit_sha) + "\n\n\n")
    #         diff = githelper.get_diff_between_commits(parent_commit, head_commit)
    #         print(diff)
    #         diff_inspector(repo, diff, head_commit)
    #         print("\n\n\n\n\n\n\n")
    #     print_stats()
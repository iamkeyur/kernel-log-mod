import logging
from datetime import datetime
import Levenshtein
from lxml import etree
import tranformation
from utils import filehelper
from utils import githelper
from utils import shellhelper
from utils import urlhelper
import config
import getloc
import unicodedata
import metrics


logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)

def diff_inspector(git_repo, commit_diff, head_commit_db):
    head_commit_sha = head_commit_db.hexsha
    #head_commit_git = git_repo.commit(head_commit_sha)
    # head_commit_db.committer_name = head_commit_git.committer.name
    # head_commit_db.committer_email = head_commit_git.committer.email
    # head_commit_db.committed_date = head_commit_git.committed_datetime
    # head_commit_db.author_name = head_commit_git.author.name
    # head_commit_db.author_email = head_commit_git.author.email
    # head_commit_db.authored_date = head_commit_git.authored_datetime
    # head_commit_db.message = head_commit_git.message

    repo_added_sloc = 0
    repo_deleted_sloc = 0
    repo_updated_sloc = 0

    repo_added_logging_loc = 0
    repo_deleted_logging_loc = 0
    repo_updated_logging_loc = 0

    for file_diff in commit_diff:
        print(file_diff.b_path + " " + file_diff.change_type)
        if file_diff.change_type == 'A':
            # file_sloc, file_logging_loc = handle_added_file(file_diff, head_commit_db)
            # repo_added_sloc += file_sloc
            # repo_added_logging_loc += file_logging_loc
            pass
        elif file_diff.change_type == 'D':
            # file_sloc, file_logging_loc = handle_deleted_file(file_diff, head_commit_db)
            # repo_deleted_sloc += file_sloc
            # repo_deleted_logging_loc += file_logging_loc
            pass
        elif file_diff.change_type == 'M' or \
                (file_diff.change_type.startswith('R') and file_diff.a_blob != file_diff.b_blob):
            # file_added_sloc, file_deleted_sloc, file_updated_sloc, file_added_logging_loc, file_deleted_logging_loc, file_updated_logging_loc = \
            #     handle_updated_file(file_diff, head_commit_db)
            handle_updated_file(file_diff, head_commit_db)

            # repo_added_sloc += file_added_sloc
            # repo_deleted_sloc += file_deleted_sloc
            # repo_updated_sloc += file_updated_sloc
            # repo_added_logging_loc += file_added_logging_loc
            # repo_deleted_logging_loc += file_deleted_logging_loc
            # repo_updated_logging_loc += file_updated_logging_loc

    # code_churn = repo_added_sloc + repo_deleted_sloc + (repo_updated_sloc * 2)
    # sloc_delta = repo_added_sloc - repo_deleted_sloc
    # logging_code_churn = repo_added_logging_loc + repo_deleted_logging_loc + (repo_updated_logging_loc * 2)
    # logging_loc_delta = repo_added_logging_loc - repo_deleted_logging_loc
    #
    # head_commit_db.code_churn = code_churn
    # head_commit_db.logging_code_churn = logging_code_churn
    # head_commit_db.save()
    #
    # return sloc_delta, logging_loc_delta



def handle_updated_file(file_diff, head_commit_db):
    file_added_sloc = 0
    file_deleted_sloc = 0
    file_updated_sloc = 0
    file_added_logging_loc = 0
    file_deleted_logging_loc = 0
    file_updated_logging_loc = 0

    if filehelper.is_c_file(file_diff.a_path) and filehelper.is_c_file(file_diff.b_path):
        c_a_file = tranformation.generate_c_file_of_blob(file_diff.a_blob)
        c_b_file = tranformation.generate_c_file_of_blob(file_diff.b_blob)
        # print(file_diff.a_path)
        # print(java_a_file)
        # with open(java_a_file) as f:
        #     read_data = f.readlines()
        # for lines in read_data:
        #     print(lines)
        loc_diff = getloc.get_java_loc_diff(c_a_file, c_b_file)
        filehelper.delete_if_exists(c_a_file)
        filehelper.delete_if_exists(c_b_file)

        file_added_sloc = loc_diff['added'].code_num
        file_deleted_sloc = loc_diff['removed'].code_num
        file_updated_sloc = loc_diff['modified'].code_num

        methods_parent = tranformation.get_methods_of_c_blob(file_diff.a_blob)
        methods_head = tranformation.get_methods_of_c_blob(file_diff.b_blob)
        # print("parents 1")
        # print(len(methods_parent))
        # for method in methods_parent:
        #     print(etree.tostring(method))

        # print("Head"
        # file_added_logging_loc, file_deleted_logging_loc, file_updated_logging_loc = \
        #     compare_all_methods(methods_parent, methods_head, file_diff, head_commit_db)
        compare_all_methods(methods_parent, methods_head, file_diff, head_commit_db)

    # if filehelper.is_c_file(file_diff.a_path) and filehelper.is_c_file(file_diff.b_path):
	#     c_a_file = tranformation.generate_java_file_of_blob(file_diff.a_blob)
    #     c_b_file = tranformation.generate_java_file_of_blob(file_diff.b_blob)
    #     # print(file_diff.a_path)
    #     # print(java_a_file)
    #     # with open(java_a_file) as f:
    #     #     read_data = f.readlines()
    #     # for lines in read_data:
    #     #     print(lines)
    #     loc_diff = getloc.get_java_loc_diff(c_a_file, c_b_file)
    #     filehelper.delete_if_exists(c_a_file)
    #     filehelper.delete_if_exists(c_b_file)

    #     file_added_sloc = loc_diff['added'].code_num
    #     file_deleted_sloc = loc_diff['removed'].code_num
    #     file_updated_sloc = loc_diff['modified'].code_num

    #     methods_parent = tranformation.get_methods_of_c_blob(file_diff.a_blob)
    #     methods_head = tranformation.get_methods_of_c_blob(file_diff.b_blob)



		
    #     #c_a_file = tranformation.generate_c_file_of_blob(file_diff.a_blob)
    #     #c_b_file = tranformation.generate_c_file_of_blob(file_diff.b_blob)
    #     # print(file_diff.a_path)
    #     # print(java_a_file)
    #     # with open(java_a_file) as f:
    #     #     read_data = f.readlines()
    #     # for lines in read_data:
    #     #     print(lines)
    #     # loc_diff = getloc.get_java_loc_diff(c_a_file, c_b_file)
    #     # filehelper.delete_if_exists(c_a_file)
    #     # filehelper.delete_if_exists(c_b_file)

    #     # file_added_sloc = loc_diff['added'].code_num
    #     # file_deleted_sloc = loc_diff['removed'].code_num
    #     # file_updated_sloc = loc_diff['modified'].code_num

    #     #methods_parent = tranformation.get_methods_of_file(c_a_file)
    #     #methods_head = tranformation.get_methods_of_file(c_b_file)
    #     #filehelper.delete_if_exists(c_a_file)
    #     #filehelper.delete_if_exists(c_b_file)
    #     # methods_parent = tranformation.get_methods_of_c_blob(file_diff.a_blob)
    #     # methods_head = tranformation.get_methods_of_c_blob(file_diff.b_blob)
    #     # for method in methods_parent:
    #     #     print(etree.tostring(method).decode(encoding='utf-8'))
    #     #
    #     # print("Head"
    #     # file_added_logging_loc, file_deleted_logging_loc, file_updated_logging_loc = \
    #     compare_all_methods(methods_parent, methods_head, file_diff, head_commit_db)
        # compare_all_methods(methods_parent, methods_head, file_diff, head_commit_db)

    # return file_added_sloc, file_deleted_sloc, file_updated_sloc, file_added_logging_loc, file_deleted_logging_loc, file_updated_logging_loc


# def handle_added_or_deleted_file(file_path, file_blob, change_type, head_commit_db: Commit):
#     file_sloc = 0
#     file_logging_loc = 0
#
#     if filehelper.is_java_file(file_path):
#         java_file = codetransform.generate_java_file_of_blob(file_blob)
#         file_sloc = getloc.get_java_sloc(java_file)
#         file_logging_loc = getloc.get_logging_loc_of_file(java_file)
#         filehelper.delete_if_exists(java_file)
#
#         if not head_commit_db.is_merge_commit:
#             methods = codetransform.get_methods_of_java_blob(file_blob)
#             for method in methods:
#                 method_str = b'<root>' + etree.tostring(method) + b'</root>'
#                 save_logs_of_method_xml_str_if_needed(change_type, file_path, head_commit_db, method_str)
#
#         if change_type == LogChangeType.ADDED_WITH_FILE:
#             logger.debug('added file: {},  sloc: {}, logging_loc: {}'.format(file_path, file_sloc, file_logging_loc))
#         elif change_type == LogChangeType.DELETED_WITH_FILE:
#             logger.debug('deleted file: {},  sloc: {}, logging_loc: {}'.format(file_path, file_sloc, file_logging_loc))
#
#     return file_sloc, file_logging_loc
#
#
# def save_logs_of_method_xml_str_if_needed(change_type, file_path, head_commit_db, method_str):
#     method = etree.fromstring(method_str)
#     method_name = codetransform.get_method_full_signature(method)
#     logging_calls = codetransform.get_logging_calls_xml_of_method(method)
#     if not head_commit_db.is_merge_commit:
#         for call_xml in logging_calls:
#             save_logs_of_logging_call_xml(call_xml, change_type, file_path, head_commit_db, method_name)
#     return len(logging_calls)
#
#
# def save_logs_of_logging_call_xml(call_xml, change_type, file_path, head_commit_db, method_name):
#     call_text = codetransform.transform_xml_str_to_code(etree.tostring(call_xml).decode('utf-8'))
#     call_name = codetransform.get_method_call_name(call_xml)
#     if '.' in call_name:
#         verbosity = call_name.split('.')[-1]
#     else:
#         verbosity = call_name
#     argument_type = get_logging_argument_type(call_xml)
#     _, verbosity_type = metrics.get_log_content_component(call_text)
#     Log.create(commit=head_commit_db, file_path=file_path, embed_method=method_name, change_type=change_type,
#                content=call_text, verbosity=verbosity, verbosity_type=verbosity_type, argument_type=argument_type)
#
#
def compare_all_methods(methods_parent, methods_head, file_diff, head_commit_db):
    file_added_logging_loc = 0
    file_deleted_logging_loc = 0
    file_updated_logging_loc = 0

    method_parent_strings = [etree.tostring(method).decode(encoding='utf-8') for method in methods_parent]
    method_head_strings = [etree.tostring(method).decode(encoding='utf-8') for method in methods_head]

    # Get methods in parent and not in head
    methods_only_in_parent = get_complement_of_a_in_b(method_head_strings, method_parent_strings)
    #methods_only_in_parent = list(map((lambda method_str: method_str), methods_only_in_parent))
    # Get methods in head and not in parent
    methods_only_in_head = get_complement_of_a_in_b(method_parent_strings, method_head_strings)
    #methods_only_in_head = list(map((lambda method_str: method_str), methods_only_in_head))

    methods_str_already_checked_in_parent = []
    methods_str_already_checked_in_head = []

    # 1. Compare methods with same signature.
    for method_parent_str in methods_only_in_parent:
        # method_parent_str = b'<root>' + method_parent_str + b'</root>'
        method_parent_xml = etree.fromstring(method_parent_str)
        for method_head_str in methods_only_in_head:
            # method_head_str = b'<root>' + method_head_str + b'</root>'
            if method_head_str in methods_str_already_checked_in_head:
                continue
            method_head_xml = etree.fromstring(method_head_str)
            is_same_name, is_same_parameters = tranformation.compare_method_signature(method_parent_xml, method_head_xml)

            if is_same_name and is_same_parameters:
                # Methods with same signature, it is modified

                logging_method_calls_in_parent = tranformation.get_logging_calls_xml_of_method(method_parent_xml)
                logging_method_calls_in_head = tranformation.get_logging_calls_xml_of_method(method_head_xml)
                method_name = tranformation.get_method_full_signature(method_head_xml)
                # for a in logging_method_calls_in_parent:
                #     print(etree.tostring(a))
                # method_added_logging_loc, method_deleted_logging_loc, method_updated_logging_loc = \
                #     compare_logging_method_calls(head_commit_db, file_diff, method_name,
                #                                  logging_method_calls_in_parent, logging_method_calls_in_head)
                compare_logging_method_calls(head_commit_db, file_diff, method_name,
                                                  logging_method_calls_in_parent, logging_method_calls_in_head)
                # file_added_logging_loc += method_added_logging_loc
                # file_deleted_logging_loc += method_deleted_logging_loc
                # file_updated_logging_loc += method_updated_logging_loc
                # methods_str_already_checked_in_parent.append(method_parent_str)
                # methods_str_already_checked_in_head.append(method_head_str)
                break

    # 2. Compare rest methods with different signature
    for method_parent_str in methods_only_in_parent:
        # method_parent_str = b'<root>' + method_parent_str + b'</root>'
        if method_parent_str in methods_str_already_checked_in_parent:
            continue
        method_parent_xml = etree.fromstring(method_parent_str)
        for method_head_str in methods_only_in_head:
            # method_head_str = b'<root>' + method_head_str + b'</root>'
            if method_head_str in methods_str_already_checked_in_head:
                continue
            method_head_xml = etree.fromstring(method_head_str)
            is_same_name, is_same_parameters = tranformation.compare_method_signature(method_parent_xml, method_head_xml)
            block_content_str_in_parent = etree.tostring(tranformation.get_method_block_content(method_parent_xml))
            block_content_str_in_head = etree.tostring(tranformation.get_method_block_content(method_head_xml))
            if is_same_name and not is_same_parameters:
                #  if method name are same, that is parameter declaration change.
                if block_content_str_in_parent == block_content_str_in_head:
                    # text are same, no need to compare
                    pass
                else:
                    # if text not same, method is modified, deal with the same process above.
                    logging_method_calls_in_parent = tranformation.get_logging_calls_xml_of_method(method_parent_xml)
                    logging_method_calls_in_head = tranformation.get_logging_calls_xml_of_method(method_head_xml)
                    method_name = tranformation.get_method_full_signature(method_head_xml)
                    # method_added_logging_loc, method_deleted_logging_loc, method_updated_logging_loc = \
                    #     compare_logging_method_calls(head_commit_db, file_diff, method_name,
                    #                                  logging_method_calls_in_parent, logging_method_calls_in_head)
                    # file_added_logging_loc += method_added_logging_loc
                    # file_deleted_logging_loc += method_deleted_logging_loc
                    # file_updated_logging_loc += method_updated_logging_loc
                    compare_logging_method_calls(head_commit_db, file_diff, method_name,
                                                 logging_method_calls_in_parent, logging_method_calls_in_head)
                methods_str_already_checked_in_parent.append(method_parent_str)
                methods_str_already_checked_in_head.append(method_head_str)
            elif not is_same_name and not is_same_parameters:
                if block_content_str_in_parent == block_content_str_in_head:
                    # if text are same, no log changed. They are renamed method.
                    methods_str_already_checked_in_parent.append(method_parent_str)
                    methods_str_already_checked_in_head.append(method_head_str)
#
#     # 3. For the rest methods, they are added or deleted
#     for method_parent_str in methods_only_in_parent:
#         # method_parent_str = b'<root>' + method_parent_str + b'</root>'
#         if method_parent_str not in methods_str_already_checked_in_parent:
#             # they are deleted, mark log calls in those methods as deleted.
#             file_deleted_logging_loc += save_logs_of_method_xml_str_if_needed(LogChangeType.DELETED_WITH_METHOD,
#                                                                               file_diff.a_path, head_commit_db, method_parent_str)
#     for method_head_str in methods_only_in_head:
#         # method_head_str = b'<root>' + method_head_str + b'</root>'
#         if method_head_str not in methods_str_already_checked_in_head:
#             # they are added, mark log calls in those methods as added.
#             file_added_logging_loc += save_logs_of_method_xml_str_if_needed(LogChangeType.ADDED_WITH_METHOD,
#                                                                             file_diff.b_path, head_commit_db, method_head_str)
#
#     return file_added_logging_loc, file_deleted_logging_loc, file_updated_logging_loc
#
#
def compare_logging_method_calls(head_commit_db, file_diff, method_name, logging_method_calls_parent, logging_method_calls_head):
    method_mapping_list = []
    method_added_logging_loc = 0
    method_deleted_logging_loc = 0
    method_updated_logging_loc = 0

    # Add index to make each call unique.
    method_calls_str_parent = \
        [str(index) + '#' + etree.tostring(call).decode('utf-8') for index, call in enumerate(logging_method_calls_parent)]
    method_calls_str_head = \
        [str(index) + '#' + etree.tostring(call).decode('utf-8') for index, call in enumerate(logging_method_calls_head)]

    for call_str_in_parent in method_calls_str_parent:
        for call_str_in_head in method_calls_str_head:
            distance_ratio = Levenshtein.ratio(tranformation.transform_xml_str_to_code(call_str_in_parent),
                                               tranformation.transform_xml_str_to_code(call_str_in_head))
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
                            mapping[2] = Levenshtein.ratio(_get_code_text_from_compare(call_str_in_parent),
                                                           _get_code_text_from_compare(call_str_in_head))
                if not is_parent_in_mapping:
                    is_head_in_mapping = False
                    for mapping in method_mapping_list:
                        call_mapping_head = mapping[1]
                        mapping_ratio = mapping[2]
                        if call_str_in_head == call_mapping_head:
                            is_head_in_mapping = True
                            if distance_ratio > mapping_ratio:
                                mapping[0] = call_str_in_parent
                                mapping[2] = Levenshtein.ratio(_get_code_text_from_compare(call_str_in_parent),
                                                               _get_code_text_from_compare(call_str_in_head))
                    if not is_head_in_mapping:
                        method_mapping_list.append([call_str_in_parent, call_str_in_head, distance_ratio])

    #print(method_mapping_list)
    method_calls_mapping_in_parent = [mapping[0] for mapping in method_mapping_list]
    method_calls_mapping_in_head = [mapping[1] for mapping in method_mapping_list]

    deleted_logging_calls_str = list(set(method_calls_str_parent) - set(method_calls_mapping_in_parent))
    added_logging_calls_str = list(set(method_calls_str_head) - set(method_calls_mapping_in_head))
    method_deleted_logging_loc += len(deleted_logging_calls_str)
    method_added_logging_loc += len(added_logging_calls_str)
#
#     if not head_commit_db.is_merge_commit:
#         for call_str in deleted_logging_calls_str:
#             call_xml = etree.fromstring(_get_code_xml_str_from_compare(call_str))
#             save_logs_of_logging_call_xml(call_xml, LogChangeType.DELETED_INSIDE_METHOD, file_diff.a_path, head_commit_db, method_name)
#
#         for call_str in added_logging_calls_str:
#             call_xml = etree.fromstring(_get_code_xml_str_from_compare(call_str))
#             save_logs_of_logging_call_xml(call_xml, LogChangeType.ADDED_INSIDE_METHOD, file_diff.b_path, head_commit_db, method_name)
#
    for mapping in method_mapping_list:
        change_from = _get_code_text_from_compare(mapping[0])
        change_to = _get_code_text_from_compare(mapping[1])

        if change_from != change_to:

            # True Update
            logging_method_parent_xml = etree.fromstring(_get_code_xml_str_from_compare(mapping[0]))
            logging_method_head_xml = etree.fromstring(_get_code_xml_str_from_compare(mapping[1]))
            update_type = None
            method_updated_logging_loc += 1

            # if not head_commit_db.is_merge_commit:
            #     call_name = tranformation.get_method_call_name(logging_method_head_xml)
                # if '.' in call_name:
                #     verbosity = call_name.split('.')[-1]
                # else:
                #     verbosity = call_name
                # _, verbosity_type = metrics.get_log_content_component(change_to)
            #argument_type = get_logging_argument_type(logging_method_head_xml)
                # print(argument_type)
            # log = Log.create(commit="", file_path=file_diff.b_path, embed_method=method_name,
            #                  change_type=LogChangeType.UPDATED, content=change_to, content_update_from=change_from,
            #                  verbosity="", verbosity_type="", argument_type=argument_type, update_type=update_type)
            print(change_to)
            print(change_from)
            #update_type = metrics.get_log_update_detail(change_from, change_to)
            #print(update_type)
                # log.is_consistent_update = is_log_consistent_update(log)
                # log.save()
#
#     return method_added_logging_loc, method_deleted_logging_loc, method_updated_logging_loc
#
#
def _get_code_xml_str_from_compare(xml_str):
    return xml_str.split('#', 1)[1]


def _get_code_text_from_compare(xml_str):
    return tranformation.transform_xml_str_to_code(_get_code_xml_str_from_compare(xml_str))


def get_complement_of_a_in_b(a_collection, b_collection):
    result = []
    for item in b_collection:
        if item not in a_collection:
            result.append(item)
    return result
#
#
def detect_project(repo, need_pull: bool, until_date: datetime):
    #e54c78a27fcdef406af799f360a93e6754adeefe
    #10004f813152646deeeb1e61a521b7ca026aa837
    #83af41947c5cbdf33c78f4818bb0cb23da39d132
    head_commit = githelper.get_spec_commit(repo, "83af41947c5cbdf33c78f4818bb0cb23da39d132")
    if head_commit.parents:
        if len(head_commit.parents) > 1:
            is_merge_commit = True

        for parent_commit in head_commit.parents:
            parent_commit_sha = parent_commit.hexsha
            print(parent_commit.hexsha)
            diff = githelper.get_diff_between_commits(parent_commit, head_commit)

            diff_inspector(repo, diff, head_commit)
    # else:
    #     # Initial Commit
    #     diff = githelper.get_diff_of_initial_commit(git_repo, head_commit)
    #     head_commit_db = Commit.get_or_create(repo=repo, commit_id=head_commit_sha)[0]
    #     if not _is_commit_analyzed(head_commit_db):
    #         diff_inspector(git_repo, diff, head_commit_db)

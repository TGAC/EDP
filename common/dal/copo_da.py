__author__ = 'felix.shaw@tgac.ac.uk - 22/10/15'

import os
from datetime import datetime, date

import copy
import re
import pandas as pd
import pymongo
from bson import ObjectId,  regex
from django.conf import settings
from django.contrib.auth.models import User
from common.dal.mongo_util import cursor_to_list, cursor_to_list_str
from common.lookup.lookup import DB_TEMPLATES
from common.schema_versions.lookup.dtol_lookups import TOL_PROFILE_TYPES
from common.utils import helpers
#from common.schemas.utils.cg_core.cg_schema_generator import CgCoreSchemas
from .copo_base_da import DAComponent, handle_dict

lg = settings.LOGGER

class Audit(DAComponent):
    def __init__(self, profile_id=None):
        super(Audit, self).__init__(profile_id, 'audit')
        self.filter = {'action': 'update','collection_name': 'SampleCollection'}
        self.projection = {}
        self.doc_included_field_lst = ['copo_id', 'manifest_id','sample_type', 'RACK_OR_PLATE_ID', 'TUBE_OR_WELL_ID']
        self.doc_excluded_field_lst = ['biosampleAccession','public_name','SPECIMEN_ID', 'sraAccession' ]

        self.update_log_addtl_fields = [*self.doc_included_field_lst, *self.doc_excluded_field_lst]
        self.update_log_addtl_fields.sort()

    def get_sample_info_based_on_audit(self, sample_id, document):
        from .sample_da import Sample

        # Fields outside the document, excluded from the 'update_log' 
        # dictionary but found in the sample
        sample = Sample().get_by_field('_id', [sample_id])

        if not sample:
            return list()
        
        sample_info = {field: sample[0].get(field, str()) for field in self.doc_excluded_field_lst if sample[0] is not None and len(sample) > 0}

        # Fields in the document but outside the 'update_log' dictionary
        audit_info = {field: document.get(field, str()) for field in self.doc_included_field_lst if field in list(document.keys())}

        out = sample_info | audit_info

        # Sort the dictionary by key
        out = {key:out[key] for key in sorted(out)}

        return out
    
    def get_sample_update_audits_field_value_lst(self, value_lst, key):
        if value_lst:
            self.filter |= {key: {'$in': value_lst}}

        cursor = cursor_to_list(
            self.get_collection_handle().find(self.filter,  self.projection))
        
        # Filter data in the 'update_log' by the field and value provided
        lst = list()
        out = list()
        data = dict()

        for element in list(cursor):
            sample_id = element.get("copo_id", ObjectId())

            audit_addtl_out = self.get_sample_info_based_on_audit(sample_id, element)
            
            for x in element.get('update_log', list()):
                # Merge the 'update_log' dictionary with the 'audit_addtl_out' dictionary
                x |= audit_addtl_out

                lst.append(x)

            if lst:
                data['update_log'] = lst
                out.append(data)
            
        return out
    
    def get_sample_update_audits_by_field_and_value(self, field, value):
        from .sample_da import Sample

        # Fields in the document but outside the 'update_log' dictionary
        if field in self.doc_included_field_lst:
            #self.projection |=  {field: 1} # Merge the projection dictionary with the field
            self.filter[field] = value

        elif field in self.doc_excluded_field_lst:
            # Fields excluded from the document and 'update_log' dictionary
            sample = Sample().get_by_field(field, [value])

            if sample is  None or len(sample) == 0:
                return list()
            
            copo_id = sample[0]['_id']
            self.filter['copo_id'] = copo_id

        else:
            # Fields in the 'update_log' dictionary
            self.filter['update_log'] = {'$elemMatch': {field: value}}

        cursor = cursor_to_list(
            self.get_collection_handle().find(self.filter, self.projection))
    
        # Filter data in the 'update_log' by the field and value provided
        lst = list()
        out = list()
        data = dict()

        for element in list(cursor):
            sample_id = element.get("copo_id", ObjectId())

            audit_addtl_out = self.get_sample_info_based_on_audit(sample_id, element)
            
            for x in element.get('update_log', list()):
                # Merge the 'update_log' dictionary with the 'audit_addtl_out' dictionary
                x |= audit_addtl_out

                if field not in self.doc_included_field_lst and field not in self.doc_excluded_field_lst:
                    if x[field] == value:
                        lst.append(x)
                else:
                    lst.append(x)

            if lst:
                data['update_log'] = lst
                out.append(data)

        return out    

    def get_sample_update_audits_by_field_updated(self, sample_type, sample_id_list, updatable_field):
        self.filter['sample_type'] = sample_type
       
        if sample_id_list:
            self.filter['update_log'] = {
                '$elemMatch': {'copo_id': {'$in': sample_id_list}, 'field': updatable_field}}
        else:
             self.filter['update_log'] = {'$elemMatch': {'field': updatable_field}}

        cursor = self.get_collection_handle().find(self.filter,  self.projection)

        # Filter data in the 'update_log' by the updatable field provided
        lst = list()
        out = list()
        data = dict()

        for element in list(cursor):
            sample_id = element.get("copo_id", ObjectId())

            audit_addtl_out = self.get_sample_info_based_on_audit(sample_id, element)
            
            for x in element.get('update_log', list()):
                if x['field'] == updatable_field:
                    # Merge the 'update_log' dictionary with the 'audit_addtl_out' dictionary
                    x |= audit_addtl_out
                    lst.append(x)

            if lst:
                data['update_log'] = lst
                out.append(data)

        return out

    def get_sample_update_audits_by_update_type(self, sample_type_list, update_type):
        if sample_type_list:
            self.filter['sample_type'] = {'$in': sample_type_list}
            self.filter['update_log'] = {
                '$elemMatch': {'update_type': update_type}}
        else:
            self.filter['update_log'] = {'$elemMatch': {'update_type': update_type}}

        cursor = cursor_to_list(
            self.get_collection_handle().find(self.filter,  self.projection))
        
        # Filter data in the 'update_log' by update type provided
        lst = list()
        out = list()
        data = dict()

        for element in list(cursor):
            sample_id = element.get("copo_id", ObjectId())

            audit_addtl_out = self.get_sample_info_based_on_audit(sample_id, element)
            
            for x in element.get('update_log', list()):
                if x['update_type'] == update_type:
                    # Merge the 'update_log' dictionary with the 'audit_addtl_out' dictionary
                    x |= audit_addtl_out

                    lst.append(x)

            if lst:
                data['update_log'] = lst
                out.append(data)

        return out

    def get_sample_update_audits_by_date(self, d_from, d_to):
        self.filter['sample_type'] = {'$in': TOL_PROFILE_TYPES}
        self.filter['update_log'] = {'$elemMatch': {
            'time_updated': {'$gte': d_from, '$lt': d_to}}}
        
        # projection = {x:1 for x in  self.doc_included_field_lst}
        # projection |= {"update_log":1} # Merge dictionaries

        cursor = cursor_to_list(
            self.get_collection_handle().find(self.filter,  self.projection).sort([['update_log.time_updated', -1]]))
        
        # Filter data in the 'update_log'
        lst = list()
        out = list()
        data = dict()

        for element in list(cursor):
            sample_id = element.get("copo_id", ObjectId())

            audit_addtl_out = self.get_sample_info_based_on_audit(sample_id, element)
            
            for x in element.get('update_log', list()):
                # Merge the 'update_log' dictionary with the 'audit_addtl_out' dictionary
                x |= audit_addtl_out

                lst.append(x)

            if lst:
                data['update_log'] = lst
                out.append(data)

        return out


class TestObjectType(DAComponent):
    def __init__(self, profile_id=None):
        super(TestObjectType, self).__init__(profile_id=profile_id, component="test")


class MetadataTemplate(DAComponent):
    def __init__(self, profile_id=None):
        super(MetadataTemplate, self).__init__(profile_id, "metadata_template")

    def update_name(self, template_name, template_id):
        record = self.get_collection_handle().update_one({"_id": ObjectId(template_id)},
                                                         {"$set": {"template_name": template_name}})
        record = self.get_by_id(template_id)
        return record

    def get_by_id(self, id):
        record = self.get_collection_handle().find_one({"_id": ObjectId(id)})
        return record

    def update_template(self, template_id, data):
        record = self.get_collection_handle().update_one(
            {"_id": ObjectId(template_id)}, {"$set": {"terms": data}})
        return record

    def get_terms_by_template_id(self, template_id):
        terms = self.get_collection_handle().find_one(
            {"_id": ObjectId(template_id)}, {"terms": 1, "_id": 0})
        return terms





class EnaFileTransfer(DAComponent):
    def __init__(self, profile_id=None):
        super(EnaFileTransfer, self).__init__(profile_id, "enaFileTransfer")
        self.profile_id = profile_id
        # self.component = str()

    def get_pending_transfers(self):
        result_list = []
        result = self.get_collection_handle().find(
            {"transfer_status": {"$ne": 2}, "status": "pending"}).limit(10)

        if result:
            result_list = list(result)
        # at most download 2 files at the sametime
        count = self.get_collection_handle().count_documents(
            {"transfer_status": 2, "status": "processing"})
        if count <= 1:
            result = self.get_collection_handle().find(
                {"transfer_status": 2, "status": "pending"}).limit(2 - count)
            if result:
                result_list.extend(list(result))
        return result_list

    def get_processing_transfers(self):
        return self.get_collection_handle().find({"transfer_status": {"$gt": 0}, "status": "processing"})

    def set_processing(self, tx_ids):
        self.get_collection_handle().update_many({"_id": {"$in": tx_ids}},
                                                {"$set": {"status": "processing",
                                                          "last_checked": helpers.get_datetime()}})

    def set_pending(self, tx_id):
        self.get_collection_handle().update_one({"_id": ObjectId(tx_id)}, {
            "$set": {"status": "pending", "last_checked": helpers.get_datetime()}})

    def set_complete(self, tx_id):
        self.get_collection_handle().update_one(
            {"_id": ObjectId(tx_id)}, {"$set": {"status": "complete","last_checked": helpers.get_datetime()}})

    def get_transfer_status_by_local_path(self, profile_id, local_paths):
        #return self.get_collection_handle().find({"profile_id"})
        result = self.get_collection_handle().find({"local_path": {"$in": local_paths}, "profile_id": profile_id},{"transfer_status":1, "local_path":1})
        result_map = {x["local_path"] : x["transfer_status"]  for x in list(result)}
        return result_map


class CopoGroup(DAComponent):
    def __init__(self):
        super(CopoGroup, self).__init__(None, "group")
        self.Group = self.get_collection_handle()

    def get_by_owner(self, owner_id):
        doc = self.Group.find({'owner_id': owner_id})
        if not doc:
            return list()
        return doc

    def get_group_names(self, owner_id=None, with_id=False):
        if not owner_id:
            owner_id = helpers.get_user_id()

        projection = {'_id': 1, 'name': 1} if with_id else {
            '_id': 0, 'name': 1}

        doc = list(self.Group.find(
            {'owner_id': owner_id}, projection))
        if not doc:
            return list()
        return doc

    def create_shared_group(self, name, description, owner_id=None):
        group_names = self.get_group_names()
        group_fields = helpers.json_to_pytype(DB_TEMPLATES['COPO_GROUP'])

        if not owner_id:
            owner_id = helpers.get_user_id()

        if any(x['name'] == name for x in group_names):
            return False  # Group name already exists
        else:
            group_fields['owner_id'] = owner_id
            group_fields['name'] = name
            group_fields['description'] = description
            group_fields['date_created'] = helpers.get_datetime().strftime(
                "%d-%m-%Y %H:%M:%S")
            # Get inserted document ID
            return self.Group.insert_one(group_fields).inserted_id

    def edit_group(self, group_id, name, description):
        update_info = {}
        group_names = self.get_group_names(with_id=True)

        update_info['name'] = name
        update_info['description'] = description
        update_info['date_modified'] = helpers.get_datetime().strftime(
            "%d-%m-%Y %H:%M:%S")

        if any(str(x['_id']) == group_id and x['name'] != name for x in group_names):
            # If edited group name is not equal to the exisiting group name
            # but the group ID is the matchES the current group ID, update the document
            self.Group.find_one_and_update({"_id": ObjectId(group_id)}, {
                "$set": update_info})
            return True
        elif any(str(x['_id']) != group_id and x['name'] == name for x in group_names):
            # If edited group name is equal to an exisiting group name
            # and the group ID does not match the current group ID, return an error
            return False  # Group name already exists
        else:
            # Update document
            self.Group.find_one_and_update({"_id": ObjectId(group_id)}, {
                "$set": update_info})
            return True

    def delete_group(self, group_id):
        result = self.Group.delete_one({'_id': ObjectId(group_id)})
        return result.deleted_count > 0

    def view_shared_group(self, group_id):
        group = cursor_to_list(self.Group.find({"_id": ObjectId(group_id)}))

        if group:
            return group[0]
        else:
            return False
        
    def get_shared_users_info_by_owner_and_profile_id(self, owner_id, profile_id):
        # Get user name and email address of the shared users of a profile
        # NB: 'member_ids' is a list of dictionaries containing user IDs
        member_ids = cursor_to_list(self.Group.find({'owner_id':owner_id,'shared_profile_ids': {'$in': [profile_id]}},{'_id':0,'member_ids':1}))
        shared_users_info = list()

        if not member_ids:
            return list()
        
        for u in member_ids:
            user_ids = u.get('member_ids',list())
            for id in user_ids:
                shared_user = User.objects.get(pk=id)
                x = {'email': shared_user.email, 'name': f"{shared_user.first_name} {shared_user.last_name}"}
                shared_users_info.append(x)
        return shared_users_info
    
    def add_profile(self, group_id, profile_id):
        return self.Group.update_one({'_id': ObjectId(group_id)}, {'$push': {'shared_profile_ids': ObjectId(profile_id)}})

    def remove_profile(self, group_id, profile_id):
        return self.Group.update_one(
            {'_id': ObjectId(group_id)},
            {'$pull': {'shared_profile_ids': ObjectId(profile_id)}}
        )

    def get_profiles_for_group_info(self, group_id):
        from .profile_da import Profile
        
        # If current logged in  user is in the 'data_manager' group i.e. 
        # if current user is a member of the  COPO development team, return all profiles
        # If not, return only the profiles for the current logged in user
        member_groups = helpers.get_group_membership_asString()
        profiles = Profile().get_profiles(search_filter=str()) if 'data_managers' in member_groups else Profile().get_for_user(helpers.get_user_id())
        p_list = cursor_to_list(profiles)

        # Sort list of profiles by 'title' key
        p_list = sorted(p_list, key=lambda x: x['title'])
        
        group = CopoGroup().get_record(group_id)
        for p in p_list:
            if p['_id'] in group['shared_profile_ids']:
                p['selected'] = True
            else:
                p['selected'] = False
        return p_list

    '''
    def get_repos_for_group_info(self, uid, group_id):
        g = CopoGroup().get_record(group_id)
        docs = cursor_to_list(Repository().Repository.find({'users.uid': uid}))
        for d in docs:
            if d['_id'] in g['repo_ids']:
                d['selected'] = True
            else:
                d['selected'] = False
        return list(docs)
    '''

    def get_users_for_group_info(self, group_id):
        group = CopoGroup().get_record(group_id)
        member_ids = group['member_ids']
        user_list = list()
        for u in member_ids:
            usr = User.objects.get(pk=u)
            x = {'id': usr.id, 'first_name': usr.first_name, 'last_name': usr.last_name, 'email': usr.email,
                 'username': usr.username}
            user_list.append(x)
        return user_list

    def add_user_to_group(self, group_id, user_id):
        return self.Group.update_one(
            {'_id': ObjectId(group_id)},
            {'$push': {'member_ids': user_id}})

    def remove_user_from_group(self, group_id, user_id):
        return self.Group.update_one(
            {'_id': ObjectId(group_id)},
            {'$pull': {'member_ids': user_id}}
        )

    def add_repo(self, group_id, repo_id):
        return self.Group.update_one({'_id': ObjectId(group_id)}, {'$push': {'repo_ids': ObjectId(repo_id)}})

    def remove_repo(self, group_id, repo_id):
        return self.Group.update_one(
            {'_id': ObjectId(group_id)},
            {'$pull': {'repo_ids': ObjectId(repo_id)}}
        )



class DataFile(DAComponent):
    def __init__(self, profile_id=None):
        super(DataFile, self).__init__(profile_id=profile_id, component="datafile" )

    def get_for_profile(self, profile_id):
        docs = self.get_collection_handle().find({
            "profile_id": profile_id
        })
        return docs

    def get_by_file_id(self, file_id=None):
        docs = None
        if file_id:
            docs = self.get_collection_handle().find_one(
                {"file_id": file_id, "deleted": helpers.get_not_deleted_flag()})

        return docs

    def get_by_file_name_id(self, file_id=None):
        docs = None
        if file_id:
            docs = self.get_collection_handle().find_one(
                {
                    "_id": ObjectId(file_id), "deleted": helpers.get_not_deleted_flag()
                },
                {
                    "name": 1
                }
            )

        return docs
    
    def get_image_filenames_by_specimen_id(self, specimen_ids):
        # Match the SPECIMEN_ID to the beginning of the image file name using regex
        specimen_ids = [regex.Regex(f'^{x}') for x in specimen_ids]
        projection = {'_id':0, 'file_location':1}
        
        filter = dict()
        filter['name'] = {'$in': specimen_ids}
        filter['bucket_name'] = {'$exists': False}
        filter['ecs_location'] = {'$exists': False}
        filter['file_location'] = {'$exists': True, '$ne': ''}
      
        cursor = self.get_collection_handle().find(filter,  projection)
        
        results = list(cursor)

        # Get values from the list of dictionaries
        image_filenames = [x for element in results for x in element.values()]

        return image_filenames
    
    def get_record_property(self, datafile_id=str(), elem=str()):
        """
        eases the access to deeply nested properties
        :param datafile_id: record id
        :param elem: schema property(key)
        :return: requested property or some default value
        """

        datafile = self.get_record(datafile_id)
        description = datafile.get("description", dict())
        description_attributes = description.get("attributes", dict())
        description_stages = description.get("stages", list())

        property_dict = dict(
            target_repository=description_attributes.get(
                "target_repository", dict()).get("deposition_context", str()),
            attach_samples=description_attributes.get(
                "attach_samples", dict()).get("study_samples", str()),
            sequencing_instrument=description_attributes.get("nucleic_acid_sequencing", dict()).get(
                "sequencing_instrument", str()),
            study_type=description_attributes.get(
                "study_type", dict()).get("study_type", str()),
            description_attributes=description_attributes,
            description_stages=description_stages
        )

        return property_dict.get(elem, str())

    def add_fields_to_datafile_stage(self, target_ids, fields, target_stage_ref):

        for target_id in target_ids:
            # for each file in target_ids retrieve the datafile object
            df = self.get_record(target_id)
            # get the stage using list comprehension and add new fields
            for idx, stage in enumerate(df['description']['stages']):
                if 'ref' in stage and stage['ref'] == target_stage_ref:
                    for field in fields:
                        df['description']['stages'][idx]['items'].append(field)

            # now update datafile record
            self.get_collection_handle().update_one({'_id': ObjectId(target_id)},
                                                    {'$set': {'description.stages': df['description']['stages']}})

    def update_file_level_metadata(self, file_id, data):
        self.get_collection_handle().update_one({"_id": ObjectId(file_id)}, {
            "$push": {"file_level_annotation": data}})
        return self.get_file_level_metadata_for_sheet(file_id, data["sheet_name"])

    def insert_sample_ids(self, file_name, sample_ids):
        self.get_collection_handle().update_one({"name": file_name}, {
            "$push": {"description.attributes.attach_samples.study_samples": {"$each": sample_ids}}})

    def update_bioimage_name(self, file_name, bioimage_name, bioimage_path):
        self.get_collection_handle().update_one({"name": file_name}, {
            "$set": {"bioimage_name": bioimage_name, "file_location": bioimage_path}})

    def get_file_level_metadata_for_sheet(self, file_id, sheetname):

        docs = self.get_collection_handle().aggregate(
            [
                {"$match": {"_id": ObjectId(file_id)}},
                {"$unwind": "$file_level_annotation"},
                {"$match": {"file_level_annotation.sheet_name": sheetname}},
                {"$project": {"file_level_annotation": 1, "_id": 0}},
                {"$sort": {"file_level_annotation.column_idx": 1}}
            ])
        return cursor_to_list(docs)

    def delete_annotation(self, col_idx, sheet_name, file_id):
        docs = self.get_collection_handle().update_one({"_id": ObjectId(file_id)},
                                                       {"$pull": {"file_level_annotation": {"sheet_name": sheet_name,
                                                                                            "column_idx": str(col_idx)}}})
        return docs

    def get_num_pending_samples(self, sub_id):
        doc = self.get_collection_handle().find_one({"_id", ObjectId(sub_id)})

    def get_records_by_field(self, field, value):
        sub = self.get_collection_handle().find({
            field: value
        })
        return cursor_to_list(sub)

    def get_records_by_fields(self, fields):
        sub = self.get_collection_handle().find(fields)
        return cursor_to_list(sub)

    def get_datafile_names_by_name_regx(self, names):
        regex_names = [re.compile(f"^{name}") for name in names]
        sub = self.get_collection_handle().find({
            "name": {"$in": regex_names}, "bioimage_name": {"$ne": ""}, "deleted": helpers.get_not_deleted_flag()
        }, {"name": 1, "_id": 0})
        datafiles = cursor_to_list(sub)
        result = [i["name"] for i in datafiles if i['name']]
        return set(result)

    def update_file_hash(self, file_oid, file_hash):
        self.get_collection_handle().update_one(
            {"_id":  file_oid}, {"$set": {"file_hash": file_hash}})






class EIChecklist(DAComponent):
    def __init__(self, profile_id=None):
        super(EIChecklist, self).__init__(profile_id=profile_id, component="eiChecklist")

    def get_checklist(self, checklist_id):
        checklists = self.execute_query({"primary_id": checklist_id})
        if checklists:
            if checklist_id == 'read':
                fields = checklists[0].get("fields", {})
                fields = {k: v for k, v in fields.items()
                          if v.get("for_dtol", True)}
                checklist = checklists[0]
                checklist["fields"] = fields
                return checklist

            return checklists[0]


    def get_sample_checklists_no_fields(self):
        return self.get_all_records_columns(filter_by={"primary_id": {"$regex": "^(ERC|read)"}},  projection={"primary_id": 1, "name": 1, "description": 1})

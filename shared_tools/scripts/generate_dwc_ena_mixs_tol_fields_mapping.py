'''
To generate the 'generate_dwc_ena_mixs_tol_fields_mapping.json' file:
    Run the command below in the 'shared_tools/scripts' directory.
    The command will generate the 'generate_dwc_ena_mixs_tol_fields_mapping.json' file  
    and save it to the '/copo/common/schema_versions/isa_mappings/' directory.

    $  python generate_dwc_ena_mixs_tol_fields_mapping.py
'''
from bs4 import BeautifulSoup
import json
import pandas as pd
import requests

# Helpers for ENA field mappings
# https://www.ebi.ac.uk/ena/submit/report/checklists/xml/*?type=sample

ENA_FIELD_NAMES_MAPPING = {
    'ASSOCIATED_BIOGENOME_PROJECTS': {
        'ena': 'associated biogenome projects'
    },
    'BARCODE_HUB': {
        'ena': 'barcoding center'
    },
    'COLLECTED_BY': {
        'ena': 'collected_by'
    },
    'COLLECTION_LOCATION_1': {
        'info': "split COLLECTION_LOCATION on first '|' and put left hand side here (should be country)",
        'ena': 'geographic location (country and/or sea)',
    },
    'COLLECTION_LOCATION_2': {
        'info': "split COLLECTION_LOCATION on first '|' and put right hand side here (should be a list of '|' separated locations)",
        'ena': 'geographic location (region and locality)',
    },
    'COLLECTOR_AFFILIATION': {
        'ena': 'collecting institution'
    },
    'COLLECTOR_ORCID_ID': {
        'ena': 'collector ORCID ID'
    },
    'CULTURE_OR_STRAIN_ID': {
        'ena': 'culture_or_strain_id'
    },
    'DATE_OF_COLLECTION': {
        'ena': 'collection date'
    },
    'DECIMAL_LATITUDE': {
        'ena': 'geographic location (latitude)'
    },
    'DECIMAL_LONGITUDE': {
        'ena': 'geographic location (longitude)'
    },
    'DEPTH': {
        'ena': 'geographic location (depth)'
    },
    'DESCRIPTION_OF_COLLECTION_METHOD': {
        'ena': 'sample collection device or method'
    },
    'DNA_VOUCHER_ID_FOR_BIOBANKING': {
        'ena': 'bio_material'
    },
    'ELEVATION': {
        'ena': 'geographic location (elevation)'
    },
    'GAL': {
        'ena': 'GAL'
    },
    'GAL_SAMPLE_ID': {
        'ena': 'GAL_sample_id'
    },
    'HABITAT': {
        'ena': 'habitat'
    },
    'IDENTIFIED_BY': {
        'ena': 'identified_by'
    },
    'IDENTIFIER_AFFILIATION': {
        'ena': 'identifier_affiliation'
    },
    'LATITUDE_END': {
        'ena': 'geographic location end (latitude_end)'
    },
    'LATITUDE_START': {
        'ena': 'geographic location start (latitude_start)'
    },
    'LIFESTAGE': {
        'ena': 'lifestage'
    },
    'LONGITUDE_END': {
        'ena': 'geographic location end (longitude_end)'
    },
    'LONGITUDE_START': {
        'ena': 'geographic location start (longitude_start)'
    },
    'ORGANISM_PART': {
        'ena': 'organism part'
    },
    'ORIGINAL_COLLECTION_DATE': {
        'ena': 'original collection date'
    },
    'ORIGINAL_DECIMAL_LATITUDE': {
        'ena': 'original geographic location (latitude)'
    },
    'ORIGINAL_DECIMAL_LONGITUDE': {
        'ena': 'original geographic location (longitude)'
    },
    'ORIGINAL_GEOGRAPHIC_LOCATION': {
        'ena': 'original collection location'
    },
    'PARTNER': {
        'ena': 'GAL'
    },
    'PARTNER_SAMPLE_ID': {
        'ena': 'GAL_sample_id'
    },
    'PROXY_TISSUE_VOUCHER_ID_FOR_BIOBANKING': {
        'ena': 'proxy biomaterial'
    },
    'PROXY_VOUCHER_ID': {
        'ena': 'proxy voucher'
    },
    'PROXY_VOUCHER_LINK': {
        'ena': 'proxy voucher url'
    },
    'RELATIONSHIP': {
        'ena': 'relationship'
    },
    'SAMPLE_COORDINATOR': {
        'ena': 'sample coordinator'
    },
    'SAMPLE_COORDINATOR_AFFILIATION': {
        'ena': 'sample coordinator affiliation'
    },
    'SAMPLE_COORDINATOR_ORCID_ID': {
        'ena': 'sample coordinator ORCID ID'
    },
    'SEX': {
        'ena': 'sex'
    },
    'SCIENTIFIC_NAME': {
        'ena': 'SCIENTIFIC_NAME'
    } ,
    'SPECIMEN_ID': {
        'ena': 'specimen_id'
    },
    'TAXON_ID': {
        'ena': 'TAXON_ID'
    }  ,
    'TISSUE_VOUCHER_ID_FOR_BIOBANKING': {
        'ena': 'bio_material'
    },
    'VOUCHER_ID': {
        'ena': 'specimen_voucher'
    },
    'VOUCHER_INSTITUTION': {
        'ena': 'voucher institution url'
    },
    'VOUCHER_LINK': {
        'ena': 'specimen voucher url'
    },
    'public_name': {
        'ena': 'tolid'
    },
    'sampleDerivedFrom': {
        'ena': 'sample derived from'
    },
    'sampleSameAs': {
        'ena': 'sample same as'
    },
    'sampleSymbiontOf': {
        'ena': 'sample symbiont of'
    }
}

ENA_AND_TOL_RULES = {
    'ASSOCIATED_TRADITIONAL_KNOWLEDGE_OR_BIOCULTURAL_PROJECT_ID':
        {
            "strict_regex": "^[a-z0-9]{8}-([a-z0-9]{4}-){3}[a-z0-9]{12}$",
            "human_readable": "[ID provided by the local context hub]"
        },
    'CHLOROPHYL_A':
        {
            "strict_regex": "^\d+$",
            "human_readable": "integer"
        },
    'COLLECTOR_ORCID_ID':
        {
            "strict_regex": "^((\d{4}-){3}\d{3}(\d|X))(\|(\d{4}-){3}\d{3}(\d|X))*|(^not provided$)|(^not applicable$)",
            "human_readable": "16-digit number that is compatible with the ISO Standard (ISO 27729),  if multiple IDs separate with a | and no spaces"
        },
    'DATE_OF_COLLECTION':
        {
            "ena_regex": "(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?"
                         "([+-][0-9]{1,2})?)?)?)?(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?"
                         "([+-][0-9]{1,2})?)?)?)?)?$)|(^not collected$)|(^not provided$)|(^restricted access$) ",
            "human_readable": "YYYY-MM-DD, YYYY-MM, YYYY, NOT_COLLECTED or NOT_PROVIDED"
        },
    'DECIMAL_LATITUDE':
        {
            "ena_regex": "(^[+-]?[0-9]+.?[0-9]*$)|(^not collected$)|(^not provided$)|(^restricted access$)",
            "human_readable": "numeric, NOT_COLLECTED or NOT_PROVIDED"
        },
    'DECIMAL_LATITUDE_ERGA':
        {
            "ena_regex": "(^[+-]?[0-9]+.?[0-9]*$)|(^not collected$)",
            "human_readable": "numeric, or NOT_COLLECTED"

        },
    'DECIMAL_LONGITUDE':
        {
            "ena_regex": "(^[+-]?[0-9]+.?[0-9]*$)|(^not collected$)|(^not provided$)|(^restricted access$)",
            "human_readable": "numeric, NOT_COLLECTED or NOT_PROVIDED"

        },
    'DECIMAL_LONGITUDE_ERGA':
        {
            "ena_regex": "(^[+-]?[0-9]+.?[0-9]*$)|(^not collected$)",
            "human_readable": "numeric, or NOT_COLLECTED"

        },
    'DEPTH':
        {
            "ena_regex": "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?",
            "human_readable": "numeric, or empty string"
        },
    'DISSOLVED_OXYGEN':
        {
            "strict_regex": "^\d+$",
            "human_readable": "integer"
        },
    'ELEVATION':
        {
            "ena_regex": "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?",
            "human_readable": "numeric, or empty string"
        },
    'ETHICS_PERMITS_FILENAME':
        {
            "optional_regex": "^.+\.pdf$",
            "human_readable": "filename (including '.pdf' extension) if permit is required or NOT_APPLICABLE if permit is not required"
        },
    'LATITUDE_END':
        {
            "ena_regex": "(^[+-]?[0-9]+.?[0-9]*$)|(^not collected$)|(^not provided$)|(^restricted access$)",
            "human_readable": "numeric, NOT_COLLECTED or NOT_PROVIDED"
        },
    'LATITUDE_END_ERGA':
        {
            "ena_regex": "(^[+-]?[0-9]+.?[0-9]*$)|(^not collected$)",
            "human_readable": "numeric, or NOT_COLLECTED"

        },
    'LATITUDE_START':
        {
            "ena_regex": "(^[+-]?[0-9]+.?[0-9]*$)|(^not collected$)|(^not provided$)|(^restricted access$)",
            "human_readable": "numeric, NOT_COLLECTED or NOT_PROVIDED"

        },
    'LATITUDE_START_ERGA':
        {

            "ena_regex": "(^[+-]?[0-9]+.?[0-9]*$)|(^not collected$)",
            "human_readable": "numeric, or NOT_COLLECTED"

        },
    'LONGITUDE_END':
        {

            "ena_regex": "(^[+-]?[0-9]+.?[0-9]*$)|(^not collected$)|(^not provided$)|(^restricted access$)",
            "human_readable": "numeric, NOT_COLLECTED or NOT_PROVIDED"

        },
    'LONGITUDE_END_ERGA':
        {
            "ena_regex": "(^[+-]?[0-9]+.?[0-9]*$)|(^not collected$)",
            "human_readable": "numeric, or NOT_COLLECTED"

        },
    'LONGITUDE_START':
        {
            "ena_regex": "(^[+-]?[0-9]+.?[0-9]*$)|(^not collected$)|(^not provided$)|(^restricted access$)",
            "human_readable": "numeric, NOT_COLLECTED or NOT_PROVIDED"
        },
    'LONGITUDE_START_ERGA':
        {
            "ena_regex": "(^[+-]?[0-9]+.?[0-9]*$)|(^not collected$)",
            "human_readable": "numeric, or NOT_COLLECTED"

        },
    'NAGOYA_PERMITS_FILENAME':
        {
            "optional_regex": "^.+\.pdf$",
            "human_readable": "filename (including '.pdf' extension) if permit is required or NOT_APPLICABLE if permit is not required"
        },
    'ORIGINAL_COLLECTION_DATE':
        {
            "ena_regex": "^[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?(/[0-9]{"
                         "4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$",
            "human_readable": "Date as YYYY, YYYY-MM or YYYY-MM-DD"
        },
    'ORIGINAL_DECIMAL_LATITUDE':
        {
            "ena_regex": "(^[+-]?[0-9]+.?[0-9]{0,8}$)",
            "human_readable": "numeric with 8 decimal places"
        },
    'ORIGINAL_DECIMAL_LONGITUDE':
        {
            "ena_regex": "(^[+-]?[0-9]+.?[0-9]{0,8}$)",
            "human_readable": "numeric with 8 decimal places"
        },
    'RACK_OR_PLATE_ID':
        {
            "optional_regex": "^[a-zA-Z]{2}\d{8}$"
        },
    'SALINITY':
        {
            "strict_regex": "^\d+$",
            "human_readable": "integer"
        },
    'SAMPLE_COORDINATOR_ORCID_ID':
        {
            "strict_regex": "^((\d{4}-){3}\d{3}(\d|X))(\|(\d{4}-){3}\d{3}(\d|X))*$",
            "human_readable": "16-digit number that is compatible with the ISO Standard (ISO 27729), if multiple IDs separate with a | and no spaces"
        },
    'SAMPLE_DERIVED_FROM':
        {
            "ena_regex": "(^[ESD]R[SR]\d{6,}(,[ESD]R[SR]\d{6,})*$)|(^SAM[END][AG]?\d+(,SAM[END][AG]?\d+)*$)|(^EGA[NR]\d{"
                         "11}(,EGA[NR]\d{11})*$)|(^[ESD]R[SR]\d{6,}-[ESD]R[SR]\d{6,}$)|(^SAM[END][AG]?\d+-SAM[END]["
                         "AG]?\d+$)|(^EGA[NR]\d{11}-EGA[NR]\d{11}$)",
            "human_readable": "Specimen accession"
        },
    'SAMPLE_SAME_AS':
        {
            "ena_regex": "(^[ESD]R[SR]\d{6,}(,[ESD]R[SR]\d{6,})*$)|(^SAM[END][AG]?\d+(,SAM[END][AG]?\d+)*$)|(^EGA[NR]\d{"
                         "11}(,EGA[NR]\d{11})*$)|(^[ESD]R[SR]\d{6,}-[ESD]R[SR]\d{6,}$)|(^SAM[END][AG]?\d+-SAM[END]["
                         "AG]?\d+$)|(^EGA[NR]\d{11}-EGA[NR]\d{11}$)",
            "human_readable": "Specimen accession"
        },
    'SAMPLE_SYMBIONT_OF':
        {
            "ena_regex": "(^[ESD]R[SR]\d{6,}(,[ESD]R[SR]\d{6,})*$)|(^SAM[END][AG]?\d+(,SAM[END][AG]?\d+)*$)|(^EGA[NR]\d{"
                         "11}(,EGA[NR]\d{11})*$)|(^[ESD]R[SR]\d{6,}-[ESD]R[SR]\d{6,}$)|(^SAM[END][AG]?\d+-SAM[END]["
                         "AG]?\d+$)|(^EGA[NR]\d{11}-EGA[NR]\d{11}$)",
            "human_readable": "Specimen accession"
        },
    'SAMPLING_PERMITS_FILENAME':
        {
            "optional_regex": "^.+\.pdf$",
            "human_readable": "filename (including '.pdf' extension) if permit is required or NOT_APPLICABLE if permit is not required"
        },
    'SAMPLING_WATER_BODY_DEPTH':
        {
            "strict_regex": "^\d+$",
            "human_readable": "integer"
        },
    'TEMPERATURE':
        {
            "strict_regex": "^\d+$",
            "human_readable": "integer"
        },
    'TIME_OF_COLLECTION':
        {
            "strict_regex": "^([0-1][0-9]|2[0-4]):[0-5]\d$",
            "human_readable": "24-hour format with hours and minutes separated by colon"
        },
    'TUBE_OR_WELL_ID':
        {
            "optional_regex": "^[a-zA-Z]{2}\d{8}$"
        },
    'WATER_SPEED':
        {
            "strict_regex": "^\d+$",
            "human_readable": "integer"
        }
}

ENA_UNITS_MAPPING = {
    'DECIMAL_LATITUDE': {'ena_unit': 'DD'},
    'DECIMAL_LONGITUDE': {'ena_unit': 'DD'},
    'DEPTH': {'ena_unit': 'm'},
    'ELEVATION': {'ena_unit': 'm'},
    'LATITUDE_END': {'ena_unit': 'DD'},
    'LATITUDE_START': {'ena_unit': 'DD'},
    'LONGITUDE_END': {'ena_unit': 'DD'},
    'LONGITUDE_START': {'ena_unit': 'DD'},
    'ORIGINAL_DECIMAL_LATITUDE': {'ena_unit': 'DD'},
    'ORIGINAL_DECIMAL_LONGITUDE': {'ena_unit': 'DD'}
}

#_______________________

# Helpers for TOL field mappings
tol_fields_lst = [
    "ASSOCIATED_BIOGENOME_PROJECTS",
    "ASSOCIATED_PROJECT_ACCESSIONS",
    "ASSOCIATED_TRADITIONAL_KNOWLEDGE_CONTACT",
    "ASSOCIATED_TRADITIONAL_KNOWLEDGE_OR_BIOCULTURAL_PROJECT_ID",
    "ASSOCIATED_TRADITIONAL_KNOWLEDGE_OR_BIOCULTURAL_RIGHTS_APPLICABLE",
    "BARCODE_HUB",
    "BARCODE_PLATE_PRESERVATIVE",
    "BARCODING_STATUS",
    "BIOBANKED_TISSUE_PRESERVATIVE",
    "CHLA",
    "COLLECTED_BY",
    "COLLECTION_LOCATION",
    "COLLECTOR_AFFILIATION",
    "COLLECTOR_ORCID_ID",
    "COLLECTOR_SAMPLE_ID",
    "COMMON_NAME",
    "CULTURE_OR_STRAIN_ID",
    "DATE_OF_COLLECTION",
    "DATE_OF_PRESERVATION",
    "DECIMAL_LATITUDE",
    "DECIMAL_LONGITUDE",
    "DEPTH",
    "DESCRIPTION_OF_COLLECTION_METHOD",
    "DIFFICULT_OR_HIGH_PRIORITY_SAMPLE",
    "DISSOLVED_OXYGEN",
    "DNA_REMOVED_FOR_BIOBANKING",
    "DNA_VOUCHER_ID_FOR_BIOBANKING",
    "ELEVATION",
    "ETHICS_PERMITS_DEF",
    "ETHICS_PERMITS_FILENAME",
    "ETHICS_PERMITS_REQUIRED",
    "FAMILY",
    "GAL",
    "GAL_SAMPLE_ID",
    "GENUS",
    "GRID_REFERENCE",
    "HABITAT",
    "HAZARD_GROUP",
    "IDENTIFIED_BY",
    "IDENTIFIED_HOW",
    "IDENTIFIER_AFFILIATION",
    "INDIGENOUS_RIGHTS_DEF",
    "INFRASPECIFIC_EPITHET",
    "LATITUDE_END",
    "LATITUDE_START",
    "LIFESTAGE",
    "LIGHT_INTENSITY",
    "LONGITUDE_END",
    "LONGITUDE_START",
    "MIXED_SAMPLE_RISK",
    "NAGOYA_PERMITS_DEF",
    "NAGOYA_PERMITS_FILENAME",
    "NAGOYA_PERMITS_REQUIRED",
    "ORDER_OR_GROUP",
    "ORGANISM_PART",
    "ORIGINAL_COLLECTION_DATE",
    "ORIGINAL_DECIMAL_LATITUDE",
    "ORIGINAL_DECIMAL_LONGITUDE",
    "ORIGINAL_GEOGRAPHIC_LOCATION",
    "OTHER_INFORMATION",
    "PH",
    "PLATE_ID_FOR_BARCODING",
    "PRESERVATION_APPROACH",
    "PRESERVATIVE_SOLUTION",
    "PRESERVED_BY",
    "PRESERVER_AFFILIATION",
    "PRIMARY_BIOGENOME_PROJECT",
    "PROXY_TISSUE_VOUCHER_ID_FOR_BIOBANKING",
    "PROXY_VOUCHER_ID",
    "PROXY_VOUCHER_LINK",
    "PURPOSE_OF_SPECIMEN",
    "RACK_OR_PLATE_ID",
    "REGULATORY_COMPLIANCE",
    "RELATIONSHIP",
    "SALINITY",
    "SAMPLE_COORDINATOR",
    "SAMPLE_COORDINATOR_AFFILIATION",
    "SAMPLE_COORDINATOR_ORCID_ID",
    "SAMPLE_FORMAT",
    "SAMPLING_PERMITS_DEF",
    "SAMPLING_PERMITS_FILENAME",
    "SAMPLING_PERMITS_REQUIRED",
    "SCIENTIFIC_NAME",
    "SERIES",
    "SEX",
    "SIZE_OF_TISSUE_IN_TUBE",
    "SPECIES_RARITY",
    "SPECIMEN_ID",
    "SPECIMEN_IDENTITY_RISK",
    "SYMBIONT",
    "TAXON_ID",
    "TAXON_REMARKS",
    "TEMPERATURE",
    "TIME_ELAPSED_FROM_COLLECTION_TO_PRESERVATION",
    "TIME_OF_COLLECTION",
    "TISSUE_FOR_BARCODING",
    "TISSUE_FOR_BIOBANKING",
    "TISSUE_REMOVED_FOR_BARCODING",
    "TISSUE_REMOVED_FOR_BIOBANKING",
    "TISSUE_VOUCHER_ID_FOR_BIOBANKING",
    "TUBE_OR_WELL_ID",
    "TUBE_OR_WELL_ID_FOR_BARCODING",
    "VOUCHER_ID",
    "VOUCHER_INSTITUTION",
    "VOUCHER_LINK",

    # "associated_tol_project",
    # "biosampleAccession",
    # "date_created",
    # "date_modified",
    # "manifest_id",
    # "manifest_version",
    # "profile_id",
    # "public_name",
    # "rack_tube",
    # "sampleDerivedFrom",
    # "sample_type",
    # "species_list",
    # "sraAccession",
    # "status",
    # "submissionAccession",
    # "time_created",
    # "time_updated",
    # "tol_project",
    # "update_type",
    # "updated_by",
]

#_______________________

# Helpers for MIxS field mappings
MIXS_FIELD_NAMES_MAPPING = {
    'COLLECTOR_SAMPLE_ID':{
        'mixs': 'samp_name'
    },
    'COMMON_NAME': {
        'mixs': 'host_common_name'
    },
    'CULTURE_OR_STRAIN_ID':{
        'mixs':'microb_start_taxID'
    },
    'DATE_OF_COLLECTION': {
        'mixs': 'collection_date'
    },
    'DECIMAL_LATITUDE': {
        'mixs': 'lat_lon'
    },
    'DECIMAL_LONGITUDE': {
        'mixs': 'lat_lon'
    },
    'DEPTH': {
        'mixs': 'depth'
    },
    'DESCRIPTION_OF_COLLECTION_METHOD': {
        'mixs': 'samp_collect_method'
    },
    'DISSOLVED_OXYGEN': {
        'mixs': 'diss_oxygen'
    },
    'ELEVATION': {
        'mixs': 'elev'
    },
    'HABITAT':{
        'mixs': 'host_body_habitat'
    },
    'LIGHT_INTENSITY':{
        'mixs': 'light_intensity'
    },
    'ORIGINAL_GEOGRAPHIC_LOCATION': {
        'mixs': 'geo_loc_name'
    },
    'OTHER_INFORMATION': {
        'mixs': 'additional_info'
    },
    'PRESERVATION_APPROACH': {
        'mixs': 'samp_preserv'
    },
    'PRESERVATIVE_SOLUTION': {
        'mixs': 'samp_store_sol'
    },
    'PH': {
        'mixs': 'ph'
    },
    'PURPOSE_OF_SPECIMEN': {
        'mixs': 'samp_purpose'
    },
    'RELATIONSHIP':{
        'mixs': 'biotic_relationship'
    },
    'SCIENTIFIC_NAME':{
        'mixs': 'specific_host'
    },
    'SIZE_OF_TISSUE_IN_TUBE': {
        'mixs': 'size_frac'
    },
    'SPECIMEN_ID': {
        'mixs':'source_mat_id'
    },
    'SEX': {
        'mixs':'urobiom_sex'
    },
    'SYMBIONT':{
        'mixs':'host_symbiont'
    },
    'TAXON_ID':
    {
        'mixs':'samp_taxon_id'
    },
    'TIME_ELAPSED_FROM_COLLECTION_TO_PRESERVATION': {
        'mixs': 'timepoint' #samp_transport_cond #samp_store_dur
    },
    'TEMPERATURE': {
        'mixs': 'samp_store_temp'
    },
    'TUBE_OR_WELL_ID': {
        'mixs': 'samp_well_name'
    },
}

def remove_duplicates_from_json(json_list):
    out = list()
    for i in json_list:
        if i not in out:
            out.append(i)
    return out

def get_mixs_field_uri():
    'html string was taken from inspecting: https://genomicsstandardsconsortium.github.io/mixs/term_list'
    
    html = """<table>
<thead>
<tr>
<th role="columnheader">Title (Name)</th>
<th role="columnheader">Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Hazard Analysis Critical Control Points (HACCP) guide food safety term (<a href="../0001215/">HACCP_term</a>)</td>
<td>Hazard Analysis Critical Control Points (HACCP) food safety terms; This field accepts terms listed under HACCP guide food safety term (<a href="http://purl.obolibrary.org/obo/FOODON_03530221">http://purl.obolibrary.org/obo/FOODON_03530221</a>)</td>
</tr>
<tr>
<td>Interagency Food Safety Analytics Collaboration (IFSAC) category (<a href="../0001179/">IFSAC_category</a>)</td>
<td>The IFSAC food categorization scheme has five distinct levels to which foods can be assigned, depending upon the type of food. First, foods are assigned to one of four food groups (aquatic animals, land animals, plants, and other). Food groups include increasingly specific food categories; dairy, eggs, meat and poultry, and game are in the land animal food group, and the category meat and poultry is further subdivided into more specific categories of meat (beef, pork, other meat) and poultry (chicken, turkey, other poultry). Finally, foods are differentiated by differences in food processing (such as pasteurized fluid dairy products, unpasteurized fluid dairy products, pasteurized solid and semi-solid dairy products, and unpasteurized solid and semi-solid dairy products. An IFSAC food category chart is available from <a href="https://www.cdc.gov/foodsafety/ifsac/projects/food-categorization-scheme.html">https://www.cdc.gov/foodsafety/ifsac/projects/food-categorization-scheme.html</a> PMID: 28926300</td>
</tr>
<tr>
<td>absolute air humidity (<a href="../0000122/">abs_air_humidity</a>)</td>
<td>Actual mass of water vapor - mh20 - present in the air water vapor mixture</td>
</tr>
<tr>
<td>adapters (<a href="../0000048/">adapters</a>)</td>
<td>Adapters provide priming sequences for both amplification and sequencing of the sample-library fragments. Both adapters should be reported; in uppercase letters</td>
</tr>
<tr>
<td>secondary and tertiary recovery methods and start date (<a href="../0001009/">add_recov_method</a>)</td>
<td>Additional (i.e. Secondary, tertiary, etc.) recovery methods deployed for increase of hydrocarbon recovery from resource and start date for each one of them. If "other" is specified, please propose entry in "additional info" field</td>
</tr>
<tr>
<td>additional info (<a href="../0000300/">additional_info</a>)</td>
<td>Information that doesn't fit anywhere else. Can also be used to propose new entries for fields with controlled vocabulary</td>
</tr>
<tr>
<td>address (<a href="../0000218/">address</a>)</td>
<td>The street name and building number where the sampling occurred</td>
</tr>
<tr>
<td>adjacent rooms (<a href="../0000219/">adj_room</a>)</td>
<td>List of rooms (room number, room name) immediately adjacent to the sampling room</td>
</tr>
<tr>
<td>environment adjacent to site (<a href="../0001121/">adjacent_environment</a>)</td>
<td>Description of the environmental system or features that are adjacent to the sampling site. This field accepts terms under ecosystem (<a href="http://purl.obolibrary.org/obo/ENVO_01001110">http://purl.obolibrary.org/obo/ENVO_01001110</a>) and human construction (<a href="http://purl.obolibrary.org/obo/ENVO_00000070">http://purl.obolibrary.org/obo/ENVO_00000070</a>). Multiple terms can be separated by pipes</td>
</tr>
<tr>
<td>aerospace structure (<a href="../0000773/">aero_struc</a>)</td>
<td>Aerospace structures typically consist of thin plates with stiffeners for the external surfaces, bulkheads and frames to support the shape and fasteners such as welds, rivets, screws and bolts to hold the components together</td>
</tr>
<tr>
<td>history/agrochemical additions (<a href="../0000639/">agrochem_addition</a>)</td>
<td>Addition of fertilizers, pesticides, etc. - amount and time of applications</td>
</tr>
<tr>
<td>air particulate matter concentration (<a href="../0000108/">air_PM_concen</a>)</td>
<td>Concentration of substances that remain suspended in the air, and comprise mixtures of organic and inorganic substances (PM10 and PM2.5); can report multiple PM's by entering numeric values preceded by name of PM</td>
</tr>
<tr>
<td>local air flow impediments (<a href="../0001146/">air_flow_impede</a>)</td>
<td>Presence of objects in the area that would influence or impede air flow through the air filter</td>
</tr>
<tr>
<td>air temperature (<a href="../0000124/">air_temp</a>)</td>
<td>Temperature of the air at the time of sampling</td>
</tr>
<tr>
<td>air temperature regimen (<a href="../0000551/">air_temp_regm</a>)</td>
<td>Information about treatment involving an exposure to varying temperatures; should include the temperature, treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include different temperature regimens</td>
</tr>
<tr>
<td>extreme_unusual_properties/Al saturation (<a href="../0000607/">al_sat</a>)</td>
<td>Aluminum saturation (esp. For tropical soils)</td>
</tr>
<tr>
<td>extreme_unusual_properties/Al saturation method (<a href="../0000324/">al_sat_meth</a>)</td>
<td>Reference or method used in determining Al saturation</td>
</tr>
<tr>
<td>alkalinity (<a href="../0000421/">alkalinity</a>)</td>
<td>Alkalinity, the ability of a solution to neutralize acids to the equivalence point of carbonate or bicarbonate</td>
</tr>
<tr>
<td>alkalinity method (<a href="../0000298/">alkalinity_method</a>)</td>
<td>Method used for alkalinity measurement</td>
</tr>
<tr>
<td>alkyl diethers (<a href="../0000490/">alkyl_diethers</a>)</td>
<td>Concentration of alkyl diethers</td>
</tr>
<tr>
<td>altitude (<a href="../0000094/">alt</a>)</td>
<td>Heights of objects such as airplanes, space shuttles, rockets, atmospheric balloons and heights of places such as atmospheric layers and clouds. It is used to measure the height of an object which is above the earth's surface. In this context, the altitude measurement is the vertical distance between the earth's surface above sea level and the sampled position in the air</td>
</tr>
<tr>
<td>aminopeptidase activity (<a href="../0000172/">aminopept_act</a>)</td>
<td>Measurement of aminopeptidase activity</td>
</tr>
<tr>
<td>ammonium (<a href="../0000427/">ammonium</a>)</td>
<td>Concentration of ammonium in the sample</td>
</tr>
<tr>
<td>amniotic fluid/color (<a href="../0000276/">amniotic_fluid_color</a>)</td>
<td>Specification of the color of the amniotic fluid sample</td>
</tr>
<tr>
<td>amount of light (<a href="../0000140/">amount_light</a>)</td>
<td>The unit of illuminance and luminous emittance, measuring luminous flux per unit area</td>
</tr>
<tr>
<td>ancestral data (<a href="../0000247/">ances_data</a>)</td>
<td>Information about either pedigree or other ancestral information description (e.g. parental variety in case of mutant or selection), e.g. A/3*B (meaning [(A x B) x B] x B)</td>
</tr>
<tr>
<td>animal water delivery method (<a href="../0001115/">anim_water_method</a>)</td>
<td>Description of the equipment or method used to distribute water to livestock. This field accepts termed listed under water delivery equipment (<a href="http://opendata.inra.fr/EOL/EOL_0001653">http://opendata.inra.fr/EOL/EOL_0001653</a>). Multiple terms can be separated by pipes</td>
</tr>
<tr>
<td>food animal antimicrobial (<a href="../0001243/">animal_am</a>)</td>
<td>The name(s) (generic or brand) of the antimicrobial(s) given to the food animal within the last 30 days</td>
</tr>
<tr>
<td>food animal antimicrobial duration (<a href="../0001244/">animal_am_dur</a>)</td>
<td>The duration of time (days) that the antimicrobial was administered to the food animal</td>
</tr>
<tr>
<td>food animal antimicrobial frequency (<a href="../0001245/">animal_am_freq</a>)</td>
<td>The frequency per day that the antimicrobial was adminstered to the food animal</td>
</tr>
<tr>
<td>food animal antimicrobial route of administration (<a href="../0001246/">animal_am_route</a>)</td>
<td>The route by which the antimicrobial is adminstered into the body of the food animal</td>
</tr>
<tr>
<td>food animal antimicrobial intended use (<a href="../0001247/">animal_am_use</a>)</td>
<td>The prescribed intended use of or the condition treated by the antimicrobial given to the food animal by any route of administration</td>
</tr>
<tr>
<td>food animal body condition (<a href="../0001248/">animal_body_cond</a>)</td>
<td>Body condition scoring is a production management tool used to evaluate overall health and nutritional needs of a food animal. Because there are different scoring systems, this field is restricted to three categories</td>
</tr>
<tr>
<td>food animal source diet (<a href="../0001130/">animal_diet</a>)</td>
<td>If the isolate is from a food animal, the type of diet eaten by the food animal.  Please list the main food staple and the setting, if appropriate.  For a list of acceptable animal feed terms or categories, please see <a href="http://www.feedipedia.org">http://www.feedipedia.org</a>.  Multiple terms may apply and can be separated by pipes</td>
</tr>
<tr>
<td>animal feeding equipment (<a href="../0001113/">animal_feed_equip</a>)</td>
<td>Description of the feeding equipment used for livestock. This field accepts terms listed under feed delivery (<a href="http://opendata.inra.fr/EOL/EOL_0001757">http://opendata.inra.fr/EOL/EOL_0001757</a>). Multiple terms can be separated by pipes</td>
</tr>
<tr>
<td>food animal group size (<a href="../0001129/">animal_group_size</a>)</td>
<td>The number of food animals of the same species that are maintained together as a unit, i.e. a herd or flock</td>
</tr>
<tr>
<td>animal housing system (<a href="../0001180/">animal_housing</a>)</td>
<td>Description of the housing system of the livestock. This field accepts terms listed under terrestrial management housing system (<a href="http://opendata.inra.fr/EOL/EOL_0001605">http://opendata.inra.fr/EOL/EOL_0001605</a>)</td>
</tr>
<tr>
<td>animal intrusion near sample source (<a href="../0001114/">animal_intrusion</a>)</td>
<td>Identification of animals intruding on the sample or sample site including invertebrates (such as pests or pollinators) and vertebrates (such as wildlife or domesticated animals). This field accepts terms under organism (<a href="http://purl.obolibrary.org/obo/NCIT_C14250">http://purl.obolibrary.org/obo/NCIT_C14250</a>). This field also accepts identification numbers from NCBI under <a href="https://www.ncbi.nlm.nih.gov/taxonomy">https://www.ncbi.nlm.nih.gov/taxonomy</a>. Multiple terms can be separated by pipes</td>
</tr>
<tr>
<td>food animal source sex category (<a href="../0001249/">animal_sex</a>)</td>
<td>The sex and reproductive status of the food animal</td>
</tr>
<tr>
<td>annotation (<a href="../0000059/">annot</a>)</td>
<td>Tool used for annotation, or for cases where annotation was provided by a community jamboree or model organism database rather than by a specific submitter</td>
</tr>
<tr>
<td>mean annual precipitation (<a href="../0000644/">annual_precpt</a>)</td>
<td>The average of all annual precipitation values known, or an estimated equivalent value derived by such methods as regional indexes or Isohyetal maps</td>
</tr>
<tr>
<td>mean annual temperature (<a href="../0000642/">annual_temp</a>)</td>
<td>Mean annual temperature</td>
</tr>
<tr>
<td>antibiotic regimen (<a href="../0000553/">antibiotic_regm</a>)</td>
<td>Information about treatment involving antibiotic administration; should include the name of antibiotic, amount administered, treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include multiple antibiotic regimens</td>
</tr>
<tr>
<td>API gravity (<a href="../0000157/">api</a>)</td>
<td>API gravity is a measure of how heavy or light a petroleum liquid is compared to water (source: <a href="https://en.wikipedia.org/wiki/API_gravity">https://en.wikipedia.org/wiki/API_gravity</a>) (e.g. 31.1   API)</td>
</tr>
<tr>
<td>architectural structure (<a href="../0000774/">arch_struc</a>)</td>
<td>An architectural structure is a human-made, free-standing, immobile outdoor construction</td>
</tr>
<tr>
<td>area sampled size (<a href="../0001255/">area_samp_size</a>)</td>
<td>The total amount or size (volume (ml), mass (g) or area (m2) ) of sample collected</td>
</tr>
<tr>
<td>aromatics wt% (<a href="../0000133/">aromatics_pc</a>)</td>
<td>Saturate, Aromatic, Resin and Asphaltene  (SARA) is an analysis method that divides  crude oil  components according to their polarizability and polarity. There are three main methods to obtain SARA results. The most popular one is known as the Iatroscan TLC-FID and is referred to as IP-143 (source: <a href="https://en.wikipedia.org/wiki/Saturate,_aromatic,_resin_and_asphaltene">https://en.wikipedia.org/wiki/Saturate,_aromatic,_resin_and_asphaltene</a>)</td>
</tr>
<tr>
<td>asphaltenes wt% (<a href="../0000135/">asphaltenes_pc</a>)</td>
<td>Saturate, Aromatic, Resin and Asphaltene  (SARA) is an analysis method that divides  crude oil  components according to their polarizability and polarity. There are three main methods to obtain SARA results. The most popular one is known as the Iatroscan TLC-FID and is referred to as IP-143 (source: <a href="https://en.wikipedia.org/wiki/Saturate,_aromatic,_resin_and_asphaltene">https://en.wikipedia.org/wiki/Saturate,_aromatic,_resin_and_asphaltene</a>)</td>
</tr>
<tr>
<td>assembly name (<a href="../0000057/">assembly_name</a>)</td>
<td>Name/version of the assembly provided by the submitter that is used in the genome browsers and in the community</td>
</tr>
<tr>
<td>assembly quality (<a href="../0000056/">assembly_qual</a>)</td>
<td>The assembly quality category is based on sets of criteria outlined for each assembly quality category. For MISAG/MIMAG; Finished: Single, validated, contiguous sequence per replicon without gaps or ambiguities with a consensus error rate equivalent to Q50 or better. High Quality Draft:Multiple fragments where gaps span repetitive regions. Presence of the large subunit (LSU) RNA, small subunit (SSU) and the presence of 5.8S rRNA or 5S rRNA depending on whether it is a eukaryotic or prokaryotic genome, respectively. Medium Quality Draft:Many fragments with little to no review of assembly other than reporting of standard assembly statistics. Low Quality Draft:Many fragments with little to no review of assembly other than reporting of standard assembly statistics. Assembly statistics include, but are not limited to total assembly size, number of contigs, contig N50/L50, and maximum contig length. For MIUVIG; Finished: Single, validated, contiguous sequence per replicon without gaps or ambiguities, with extensive manual review and editing to annotate putative gene functions and transcriptional units. High-quality draft genome: One or multiple fragments, totaling   90% of the expected genome or replicon sequence or predicted complete. Genome fragment(s): One or multiple fragments, totalling &lt; 90% of the expected genome or replicon sequence, or for which no genome size could be estimated</td>
</tr>
<tr>
<td>assembly software (<a href="../0000058/">assembly_software</a>)</td>
<td>Tool(s) used for assembly, including version number and parameters</td>
</tr>
<tr>
<td>relevant electronic resources (<a href="../0000091/">associated_resource</a>)</td>
<td>A related resource that is referenced, cited, or otherwise associated to the sequence</td>
</tr>
<tr>
<td>duration of association with the host (<a href="../0001299/">association_duration</a>)</td>
<td>Time spent in host of the symbiotic organism at the time of sampling; relevant scale depends on symbiotic organism and study</td>
</tr>
<tr>
<td>atmospheric data (<a href="../0001097/">atmospheric_data</a>)</td>
<td>Measurement of atmospheric data; can include multiple data</td>
</tr>
<tr>
<td>average dew point (<a href="../0000141/">avg_dew_point</a>)</td>
<td>The average of dew point measures taken at the beginning of every hour over a 24 hour period on the sampling day</td>
</tr>
<tr>
<td>average daily occupancy (<a href="../0000775/">avg_occup</a>)</td>
<td>Daily average occupancy of room. Indicate the number of person(s) daily occupying the sampling room</td>
</tr>
<tr>
<td>average temperature (<a href="../0000142/">avg_temp</a>)</td>
<td>The average of temperatures taken at the beginning of every hour over a 24 hour period on the sampling day</td>
</tr>
<tr>
<td>bacterial production (<a href="../0000683/">bac_prod</a>)</td>
<td>Bacterial production in the water column measured by isotope uptake</td>
</tr>
<tr>
<td>bacterial respiration (<a href="../0000684/">bac_resp</a>)</td>
<td>Measurement of bacterial respiration in the water column</td>
</tr>
<tr>
<td>bacterial carbon production (<a href="../0000173/">bacteria_carb_prod</a>)</td>
<td>Measurement of bacterial carbon production</td>
</tr>
<tr>
<td>bacteria density (<a href="../0001194/">bacterial_density</a>)</td>
<td>Number of bacteria in sample, as defined by bacteria density (<a href="http://purl.obolibrary.org/obo/GENEPIO_0000043">http://purl.obolibrary.org/obo/GENEPIO_0000043</a>)</td>
</tr>
<tr>
<td>barometric pressure (<a href="../0000096/">barometric_press</a>)</td>
<td>Force per unit area exerted against a surface by the weight of air above that surface</td>
</tr>
<tr>
<td>basin name (<a href="../0000290/">basin</a>)</td>
<td>Name of the basin (e.g. Campos)</td>
</tr>
<tr>
<td>bathroom count (<a href="../0000776/">bathroom_count</a>)</td>
<td>The number of bathrooms in the building</td>
</tr>
<tr>
<td>bedroom count (<a href="../0000777/">bedroom_count</a>)</td>
<td>The number of bedrooms in the building</td>
</tr>
<tr>
<td>benzene (<a href="../0000153/">benzene</a>)</td>
<td>Concentration of benzene in the sample</td>
</tr>
<tr>
<td>binning parameters (<a href="../0000077/">bin_param</a>)</td>
<td>The parameters that have been applied during the extraction of genomes from metagenomic datasets</td>
</tr>
<tr>
<td>binning software (<a href="../0000078/">bin_software</a>)</td>
<td>Tool(s) used for the extraction of genomes from metagenomic datasets, where possible include a product ID (PID) of the tool(s) used</td>
</tr>
<tr>
<td>biochemical oxygen demand (<a href="../0000653/">biochem_oxygen_dem</a>)</td>
<td>Amount of dissolved oxygen needed by aerobic biological organisms in a body of water to break down organic material present in a given water sample at certain temperature over a specific time period</td>
</tr>
<tr>
<td>biocide administration (<a href="../0001011/">biocide</a>)</td>
<td>List of biocides (commercial name of product and supplier) and date of administration</td>
</tr>
<tr>
<td>biocide administration method (<a href="../0000456/">biocide_admin_method</a>)</td>
<td>Method of biocide administration (dose, frequency, duration, time elapsed between last biociding and sampling) (e.g. 150 mg/l; weekly; 4 hr; 3 days)</td>
</tr>
<tr>
<td>biocide (<a href="../0001258/">biocide_used</a>)</td>
<td>Substance intended for preventing, neutralizing, destroying, repelling, or mitigating the effects of any pest or microorganism; that inhibits the growth, reproduction, and activity of organisms, including fungal cells; decreases the number of fungi or pests present; deters microbial growth and degradation of other ingredients in the formulation. Indicate the biocide used on the location where the sample was taken. Multiple terms can be separated by pipes</td>
</tr>
<tr>
<td>biological status (<a href="../0000858/">biol_stat</a>)</td>
<td>The level of genome modification</td>
</tr>
<tr>
<td>biomass (<a href="../0000174/">biomass</a>)</td>
<td>Amount of biomass; should include the name for the part of biomass measured, e.g. Microbial, total. Can include multiple measurements</td>
</tr>
<tr>
<td>biotic regimen (<a href="../0001038/">biotic_regm</a>)</td>
<td>Information about treatment(s) involving use of biotic factors, such as bacteria, viruses or fungi</td>
</tr>
<tr>
<td>observed biotic relationship (<a href="../0000028/">biotic_relationship</a>)</td>
<td>Description of relationship(s) between the subject organism and other organism(s) it is associated with. E.g., parasite on species X; mutualist with species Y. The target organism is the subject of the relationship, and the other organism(s) is the object</td>
</tr>
<tr>
<td>birth control (<a href="../0000286/">birth_control</a>)</td>
<td>Specification of birth control medication used</td>
</tr>
<tr>
<td>bishomohopanol (<a href="../0000175/">bishomohopanol</a>)</td>
<td>Concentration of bishomohopanol</td>
</tr>
<tr>
<td>blood/blood disorder (<a href="../0000271/">blood_blood_disord</a>)</td>
<td>History of blood disorders; can include multiple disorders.  The terms should be chosen from the DO (Human Disease Ontology) at <a href="http://www.disease-ontology.org">http://www.disease-ontology.org</a>, hematopoietic system disease (<a href="https://disease-ontology.org/?id=DOID:74">https://disease-ontology.org/?id=DOID:74</a>)</td>
</tr>
<tr>
<td>host blood pressure diastolic (<a href="../0000258/">blood_press_diast</a>)</td>
<td>Resting diastolic blood pressure, measured as mm mercury</td>
</tr>
<tr>
<td>host blood pressure systolic (<a href="../0000259/">blood_press_syst</a>)</td>
<td>Resting systolic blood pressure, measured as mm mercury</td>
</tr>
<tr>
<td>bromide (<a href="../0000176/">bromide</a>)</td>
<td>Concentration of bromide</td>
</tr>
<tr>
<td>design, construction, and operation documents (<a href="../0000787/">build_docs</a>)</td>
<td>The building design, construction and operation documents</td>
</tr>
<tr>
<td>building occupancy type (<a href="../0000761/">build_occup_type</a>)</td>
<td>The primary function for which a building or discrete part of a building is intended to be used</td>
</tr>
<tr>
<td>building setting (<a href="../0000768/">building_setting</a>)</td>
<td>A location (geography) where a building is set</td>
</tr>
<tr>
<td>built structure age (<a href="../0000145/">built_struc_age</a>)</td>
<td>The age of the built structure since construction</td>
</tr>
<tr>
<td>built structure setting (<a href="../0000778/">built_struc_set</a>)</td>
<td>The characterization of the location of the built structure as high or low human density</td>
</tr>
<tr>
<td>built structure type (<a href="../0000721/">built_struc_type</a>)</td>
<td>A physical structure that is a body or assemblage of bodies in space to form a system capable of supporting loads</td>
</tr>
<tr>
<td>calcium (<a href="../0000432/">calcium</a>)</td>
<td>Concentration of calcium in the sample</td>
</tr>
<tr>
<td>carbon dioxide (<a href="../0000097/">carb_dioxide</a>)</td>
<td>Carbon dioxide (gas) amount or concentration at the time of sampling</td>
</tr>
<tr>
<td>carbon monoxide (<a href="../0000098/">carb_monoxide</a>)</td>
<td>Carbon monoxide (gas) amount or concentration at the time of sampling</td>
</tr>
<tr>
<td>carbon/nitrogen ratio (<a href="../0000310/">carb_nitro_ratio</a>)</td>
<td>Ratio of amount or concentrations of carbon to nitrogen</td>
</tr>
<tr>
<td>ceiling area (<a href="../0000148/">ceil_area</a>)</td>
<td>The area of the ceiling space within the room</td>
</tr>
<tr>
<td>ceiling condition (<a href="../0000779/">ceil_cond</a>)</td>
<td>The physical condition of the ceiling at the time of sampling; photos or video preferred; use drawings to indicate location of damaged areas</td>
</tr>
<tr>
<td>ceiling finish material (<a href="../0000780/">ceil_finish_mat</a>)</td>
<td>The type of material used to finish a ceiling</td>
</tr>
<tr>
<td>ceiling structure (<a href="../0000782/">ceil_struc</a>)</td>
<td>The construction format of the ceiling</td>
</tr>
<tr>
<td>ceiling texture (<a href="../0000783/">ceil_texture</a>)</td>
<td>The feel, appearance, or consistency of a ceiling surface</td>
</tr>
<tr>
<td>ceiling thermal mass (<a href="../0000143/">ceil_thermal_mass</a>)</td>
<td>The ability of the ceiling to provide inertia against temperature fluctuations. Generally this means concrete that is exposed. A metal deck that supports a concrete slab will act thermally as long as it is exposed to room air flow</td>
</tr>
<tr>
<td>ceiling type (<a href="../0000784/">ceil_type</a>)</td>
<td>The type of ceiling according to the ceiling's appearance or construction</td>
</tr>
<tr>
<td>ceiling signs of water/mold (<a href="../0000781/">ceil_water_mold</a>)</td>
<td>Signs of the presence of mold or mildew on the ceiling</td>
</tr>
<tr>
<td>chemical administration (<a href="../0000751/">chem_administration</a>)</td>
<td>List of chemical compounds administered to the host or site where sampling occurred, and when (e.g. Antibiotics, n fertilizer, air filter); can include multiple compounds. For chemical entities of biological interest ontology (chebi) (v 163), <a href="http://purl.bioontology.org/ontology/chebi">http://purl.bioontology.org/ontology/chebi</a></td>
</tr>
<tr>
<td>chemical mutagen (<a href="../0000555/">chem_mutagen</a>)</td>
<td>Treatment involving use of mutagens; should include the name of mutagen, amount administered, treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include multiple mutagen regimens</td>
</tr>
<tr>
<td>chemical oxygen demand (<a href="../0000656/">chem_oxygen_dem</a>)</td>
<td>A measure of the capacity of water to consume oxygen during the decomposition of organic matter and the oxidation of inorganic chemicals such as ammonia and nitrite</td>
</tr>
<tr>
<td>chemical treatment method (<a href="../0000457/">chem_treat_method</a>)</td>
<td>Method of chemical administration(dose, frequency, duration, time elapsed between administration and sampling) (e.g. 50 mg/l; twice a week; 1 hr; 0 days)</td>
</tr>
<tr>
<td>chemical treatment (<a href="../0001012/">chem_treatment</a>)</td>
<td>List of chemical compounds administered upstream the sampling location where sampling occurred (e.g. Glycols, H2S scavenger, corrosion and scale inhibitors, demulsifiers, and other production chemicals etc.). The commercial name of the product and name of the supplier should be provided. The date of administration should also be included</td>
</tr>
<tr>
<td>chimera check software (<a href="../0000052/">chimera_check</a>)</td>
<td>Tool(s) used for chimera checking, including version number and parameters, to discover and remove chimeric sequences. A chimeric sequence is comprised of two or more phylogenetically distinct parent sequences</td>
</tr>
<tr>
<td>chloride (<a href="../0000429/">chloride</a>)</td>
<td>Concentration of chloride in the sample</td>
</tr>
<tr>
<td>chlorophyll (<a href="../0000177/">chlorophyll</a>)</td>
<td>Concentration of chlorophyll</td>
</tr>
<tr>
<td>climate environment (<a href="../0001040/">climate_environment</a>)</td>
<td>Treatment involving an exposure to a particular climate; treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include multiple climates</td>
</tr>
<tr>
<td>collection site geographic feature (<a href="../0001183/">coll_site_geo_feat</a>)</td>
<td>Text or terms that describe the geographic feature where the food sample was obtained by the researcher. This field accepts selected terms listed under the following ontologies: anthropogenic geographic feature (<a href="http://purl.obolibrary.org/obo/ENVO_00000002">http://purl.obolibrary.org/obo/ENVO_00000002</a>), for example agricultural fairground [ENVO:01000986]; garden [ENVO:00000011} or any of its subclasses; market [ENVO:01000987]; water well [ENVO:01000002]; or human construction (<a href="http://purl.obolibrary.org/obo/ENVO_00000070">http://purl.obolibrary.org/obo/ENVO_00000070</a>)</td>
</tr>
<tr>
<td>collection date (<a href="../0000011/">collection_date</a>)</td>
<td>The time of sampling, either as an instance (single point in time) or interval. In case no exact time is available, the date/time can be right truncated i.e. all of these are valid times: 2008-01-23T19:23:10+00:00; 2008-01-23T19:23:10; 2008-01-23; 2008-01; 2008; Except: 2008-01; 2008 all are ISO8601 compliant</td>
</tr>
<tr>
<td>completeness approach (<a href="../0000071/">compl_appr</a>)</td>
<td>The approach used to determine the completeness of a given genomic assembly, which would typically make use of a set of conserved marker genes or a closely related reference genome. For UViG completeness, include reference genome or group used, and contig feature suggesting a complete genome</td>
</tr>
<tr>
<td>completeness score (<a href="../0000069/">compl_score</a>)</td>
<td>Completeness score is typically based on either the fraction of markers found as compared to a database or the percent of a genome found as compared to a closely related reference genome. High Quality Draft: &gt;90%, Medium Quality Draft: &gt;50%, and Low Quality Draft: &lt; 50% should have the indicated completeness scores</td>
</tr>
<tr>
<td>completeness software (<a href="../0000070/">compl_software</a>)</td>
<td>Tools used for completion estimate, i.e. checkm, anvi'o, busco</td>
</tr>
<tr>
<td>conductivity (<a href="../0000692/">conduc</a>)</td>
<td>Electrical conductivity of water</td>
</tr>
<tr>
<td>food stored by consumer (storage duration) (<a href="../0001195/">cons_food_stor_dur</a>)</td>
<td>The storage duration of the food commodity by the consumer, prior to onset of illness or sample collection.  Indicate the timepoint written in ISO 8601 format</td>
</tr>
<tr>
<td>food stored by consumer (storage temperature) (<a href="../0001196/">cons_food_stor_temp</a>)</td>
<td>Temperature at which food commodity was stored by the consumer, prior to onset of illness or sample collection</td>
</tr>
<tr>
<td>purchase date (<a href="../0001197/">cons_purch_date</a>)</td>
<td>The date a food product was purchased by consumer</td>
</tr>
<tr>
<td>quantity purchased (<a href="../0001198/">cons_qty_purchased</a>)</td>
<td>The quantity of food purchased by consumer</td>
</tr>
<tr>
<td>contamination score (<a href="../0000072/">contam_score</a>)</td>
<td>The contamination score is based on the fraction of single-copy genes that are observed more than once in a query genome. The following scores are acceptable for; High Quality Draft: &lt; 5%, Medium Quality Draft: &lt; 10%, Low Quality Draft: &lt; 10%. Contamination must be below 5% for a SAG or MAG to be deposited into any of the public databases</td>
</tr>
<tr>
<td>contamination screening input (<a href="../0000005/">contam_screen_input</a>)</td>
<td>The type of sequence data used as input</td>
</tr>
<tr>
<td>contamination screening parameters (<a href="../0000073/">contam_screen_param</a>)</td>
<td>Specific parameters used in the decontamination sofware, such as reference database, coverage, and kmers. Combinations of these parameters may also be used, i.e. kmer and coverage, or reference database and kmer</td>
</tr>
<tr>
<td>cooling system identifier (<a href="../0000785/">cool_syst_id</a>)</td>
<td>The cooling system identifier</td>
</tr>
<tr>
<td>history/crop rotation (<a href="../0000318/">crop_rotation</a>)</td>
<td>Whether or not crop is rotated, and if yes, rotation schedule</td>
</tr>
<tr>
<td>crop yield (<a href="../0001116/">crop_yield</a>)</td>
<td>Amount of crop produced per unit or area of land</td>
</tr>
<tr>
<td>culture isolation date (<a href="../0001181/">cult_isol_date</a>)</td>
<td>The datetime marking the end of a process in which a sample yields a positive result for the target microbial analyte(s) in the form of an isolated colony or colonies</td>
</tr>
<tr>
<td>culture result (<a href="../0001117/">cult_result</a>)</td>
<td>Any result of a bacterial culture experiment reported as a binary assessment such as positive/negative, active/inactive</td>
</tr>
<tr>
<td>culture result organism (<a href="../0001118/">cult_result_org</a>)</td>
<td>Taxonomic information about the cultured organism(s)</td>
</tr>
<tr>
<td>culture rooting medium (<a href="../0001041/">cult_root_med</a>)</td>
<td>Name or reference for the hydroponic or in vitro culture rooting medium; can be the name of a commonly used medium or reference to a specific medium, e.g. Murashige and Skoog medium. If the medium has not been formally published, use the rooting medium descriptors</td>
</tr>
<tr>
<td>culture target microbial analyte (<a href="../0001119/">cult_target</a>)</td>
<td>The target microbial analyte in terms of investigation scope. This field accepts terms under organism (<a href="http://purl.obolibrary.org/obo/NCIT_C14250">http://purl.obolibrary.org/obo/NCIT_C14250</a>). This field also accepts identification numbers from NCBI under <a href="https://www.ncbi.nlm.nih.gov/taxonomy">https://www.ncbi.nlm.nih.gov/taxonomy</a></td>
</tr>
<tr>
<td>current land use (<a href="../0001080/">cur_land_use</a>)</td>
<td>Present state of sample site</td>
</tr>
<tr>
<td>current vegetation (<a href="../0000312/">cur_vegetation</a>)</td>
<td>Vegetation classification from one or more standard classification systems, or agricultural crop</td>
</tr>
<tr>
<td>current vegetation method (<a href="../0000314/">cur_vegetation_meth</a>)</td>
<td>Reference or method used in vegetation classification</td>
</tr>
<tr>
<td>extreme weather date (<a href="../0001142/">date_extr_weath</a>)</td>
<td>Date of unusual weather events that may have affected microbial populations. Multiple terms can be separated by pipes, listed in reverse chronological order</td>
</tr>
<tr>
<td>date last rain (<a href="../0000786/">date_last_rain</a>)</td>
<td>The date of the last time it rained</td>
</tr>
<tr>
<td>decontamination software (<a href="../0000074/">decontam_software</a>)</td>
<td>Tool(s) used in contamination screening</td>
</tr>
<tr>
<td>density (<a href="../0000435/">density</a>)</td>
<td>Density of the sample, which is its mass per unit volume (aka volumetric mass density)</td>
</tr>
<tr>
<td>depositional environment (<a href="../0000992/">depos_env</a>)</td>
<td>Main depositional environment (<a href="https://en.wikipedia.org/wiki/Depositional_environment">https://en.wikipedia.org/wiki/Depositional_environment</a>). If "other" is specified, please propose entry in "additional info" field</td>
</tr>
<tr>
<td>depth (<a href="../0000018/">depth</a>)</td>
<td>The vertical distance below local surface. For sediment or soil samples depth is measured from sediment or soil surface, respectively. Depth can be reported as an interval for subsurface samples</td>
</tr>
<tr>
<td>dermatology disorder (<a href="../0000284/">dermatology_disord</a>)</td>
<td>History of dermatology disorders; can include multiple disorders. The terms should be chosen from the DO (Human Disease Ontology) at <a href="http://www.disease-ontology.org">http://www.disease-ontology.org</a>, skin disease (<a href="https://disease-ontology.org/?id=DOID:37">https://disease-ontology.org/?id=DOID:37</a>)</td>
</tr>
<tr>
<td>detection type (<a href="../0000084/">detec_type</a>)</td>
<td>Type of UViG detection</td>
</tr>
<tr>
<td>dew point (<a href="../0000129/">dew_point</a>)</td>
<td>The temperature to which a given parcel of humid air must be cooled, at constant barometric pressure, for water vapor to condense into water</td>
</tr>
<tr>
<td>major diet change in last six months (<a href="../0000266/">diet_last_six_month</a>)</td>
<td>Specification of major diet changes in the last six months, if yes the change should be specified</td>
</tr>
<tr>
<td>dietary claim or use (<a href="../0001199/">dietary_claim_use</a>)</td>
<td>These descriptors are used either for foods intended for special dietary use as defined in 21 CFR 105 or for foods that have special characteristics indicated in the name or labeling. This field accepts terms listed under dietary claim or use (<a href="http://purl.obolibrary.org/obo/FOODON_03510023">http://purl.obolibrary.org/obo/FOODON_03510023</a>). Multiple terms can be separated by one or more pipes, but please consider limiting this list to the most prominent dietary claim or use</td>
</tr>
<tr>
<td>diether lipids (<a href="../0000178/">diether_lipids</a>)</td>
<td>Concentration of diether lipids; can include multiple types of diether lipids</td>
</tr>
<tr>
<td>dissolved carbon dioxide (<a href="../0000436/">diss_carb_dioxide</a>)</td>
<td>Concentration of dissolved carbon dioxide in the sample or liquid portion of the sample</td>
</tr>
<tr>
<td>dissolved hydrogen (<a href="../0000179/">diss_hydrogen</a>)</td>
<td>Concentration of dissolved hydrogen</td>
</tr>
<tr>
<td>dissolved inorganic carbon (<a href="../0000434/">diss_inorg_carb</a>)</td>
<td>Dissolved inorganic carbon concentration in the sample, typically measured after filtering the sample using a 0.45 micrometer filter</td>
</tr>
<tr>
<td>dissolved inorganic nitrogen (<a href="../0000698/">diss_inorg_nitro</a>)</td>
<td>Concentration of dissolved inorganic nitrogen</td>
</tr>
<tr>
<td>dissolved inorganic phosphorus (<a href="../0000106/">diss_inorg_phosp</a>)</td>
<td>Concentration of dissolved inorganic phosphorus in the sample</td>
</tr>
<tr>
<td>dissolved iron (<a href="../0000139/">diss_iron</a>)</td>
<td>Concentration of dissolved iron in the sample</td>
</tr>
<tr>
<td>dissolved organic carbon (<a href="../0000433/">diss_org_carb</a>)</td>
<td>Concentration of dissolved organic carbon in the sample, liquid portion of the sample, or aqueous phase of the fluid</td>
</tr>
<tr>
<td>dissolved organic nitrogen (<a href="../0000162/">diss_org_nitro</a>)</td>
<td>Dissolved organic nitrogen concentration measured as; total dissolved nitrogen - NH4 - NO3 - NO2</td>
</tr>
<tr>
<td>dissolved oxygen (<a href="../0000119/">diss_oxygen</a>)</td>
<td>Concentration of dissolved oxygen</td>
</tr>
<tr>
<td>dissolved oxygen in fluids (<a href="../0000438/">diss_oxygen_fluid</a>)</td>
<td>Concentration of dissolved oxygen in the oil field produced fluids as it contributes to oxgen-corrosion and microbial activity (e.g. Mic)</td>
</tr>
<tr>
<td>dominant hand (<a href="../0000944/">dominant_hand</a>)</td>
<td>Dominant hand of the subject</td>
</tr>
<tr>
<td>door type, composite (<a href="../0000795/">door_comp_type</a>)</td>
<td>The composite type of the door</td>
</tr>
<tr>
<td>door condition (<a href="../0000788/">door_cond</a>)</td>
<td>The phsical condition of the door</td>
</tr>
<tr>
<td>door direction of opening (<a href="../0000789/">door_direct</a>)</td>
<td>The direction the door opens</td>
</tr>
<tr>
<td>door location (<a href="../0000790/">door_loc</a>)</td>
<td>The relative location of the door in the room</td>
</tr>
<tr>
<td>door material (<a href="../0000791/">door_mat</a>)</td>
<td>The material the door is composed of</td>
</tr>
<tr>
<td>door movement (<a href="../0000792/">door_move</a>)</td>
<td>The type of movement of the door</td>
</tr>
<tr>
<td>door area or size (<a href="../0000158/">door_size</a>)</td>
<td>The size of the door</td>
</tr>
<tr>
<td>door type (<a href="../0000794/">door_type</a>)</td>
<td>The type of door material</td>
</tr>
<tr>
<td>door type, metal (<a href="../0000796/">door_type_metal</a>)</td>
<td>The type of metal door</td>
</tr>
<tr>
<td>door type, wood (<a href="../0000797/">door_type_wood</a>)</td>
<td>The type of wood door</td>
</tr>
<tr>
<td>door signs of water/mold (<a href="../0000793/">door_water_mold</a>)</td>
<td>Signs of the presence of mold or mildew on a door</td>
</tr>
<tr>
<td>douche (<a href="../0000967/">douche</a>)</td>
<td>Date of most recent douche</td>
</tr>
<tr>
<td>downward PAR (<a href="../0000703/">down_par</a>)</td>
<td>Visible waveband radiance and irradiance measurements in the water column</td>
</tr>
<tr>
<td>drainage classification (<a href="../0001085/">drainage_class</a>)</td>
<td>Drainage classification from a standard system such as the USDA system</td>
</tr>
<tr>
<td>drawings (<a href="../0000798/">drawings</a>)</td>
<td>The buildings architectural drawings; if design is chosen, indicate phase-conceptual, schematic, design development, and construction documents</td>
</tr>
<tr>
<td>drug usage (<a href="../0000894/">drug_usage</a>)</td>
<td>Any drug used by subject and the frequency of usage; can include multiple drugs used</td>
</tr>
<tr>
<td>efficiency percent (<a href="../0000657/">efficiency_percent</a>)</td>
<td>Percentage of volatile solids removed from the anaerobic digestor</td>
</tr>
<tr>
<td>elevation (<a href="../0000093/">elev</a>)</td>
<td>Elevation of the sampling site is its height above a fixed reference point, most commonly the mean sea level. Elevation is mainly used when referring to points on the earth's surface, while altitude is used for points above the surface, such as an aircraft in flight or a spacecraft in orbit</td>
</tr>
<tr>
<td>elevator count (<a href="../0000799/">elevator</a>)</td>
<td>The number of elevators within the built structure</td>
</tr>
<tr>
<td>emulsions (<a href="../0000660/">emulsions</a>)</td>
<td>Amount or concentration of substances such as paints, adhesives, mayonnaise, hair colorants, emulsified oils, etc.; can include multiple emulsion types</td>
</tr>
<tr>
<td>encoded traits (<a href="../0000034/">encoded_traits</a>)</td>
<td>Should include key traits like antibiotic resistance or xenobiotic degradation phenotypes for plasmids, converting genes for phage</td>
</tr>
<tr>
<td>enrichment protocol (<a href="../0001177/">enrichment_protocol</a>)</td>
<td>The microbiological workflow or protocol followed to test for the presence or enumeration of the target microbial analyte(s). Please provide a PubMed or DOI reference for published protocols</td>
</tr>
<tr>
<td>broad-scale environmental context (<a href="../0000012/">env_broad_scale</a>)</td>
<td>Report the major environmental system the sample or specimen came from. The system(s) identified should have a coarse spatial grain, to provide the general environmental context of where the sampling was done (e.g. in the desert or a rainforest). We recommend using subclasses of EnvO s biome class:  <a href="http://purl.obolibrary.org/obo/ENVO_00000428">http://purl.obolibrary.org/obo/ENVO_00000428</a>. EnvO documentation about how to use the field: <a href="https://github.com/EnvironmentOntology/envo/wiki/Using-ENVO-with-MIxS">https://github.com/EnvironmentOntology/envo/wiki/Using-ENVO-with-MIxS</a></td>
</tr>
<tr>
<td>local environmental context (<a href="../0000013/">env_local_scale</a>)</td>
<td>Report the entity or entities which are in the sample or specimen s local vicinity and which you believe have significant causal influences on your sample or specimen. We recommend using EnvO terms which are of smaller spatial grain than your entry for env_broad_scale. Terms, such as anatomical sites, from other OBO Library ontologies which interoperate with EnvO (e.g. UBERON) are accepted in this field. EnvO documentation about how to use the field: <a href="https://github.com/EnvironmentOntology/envo/wiki/Using-ENVO-with-MIxS">https://github.com/EnvironmentOntology/envo/wiki/Using-ENVO-with-MIxS</a></td>
</tr>
<tr>
<td>environmental medium (<a href="../0000014/">env_medium</a>)</td>
<td>Report the environmental material(s) immediately surrounding the sample or specimen at the time of sampling. We recommend using subclasses of 'environmental material' (<a href="http://purl.obolibrary.org/obo/ENVO_00010483">http://purl.obolibrary.org/obo/ENVO_00010483</a>). EnvO documentation about how to use the field: <a href="https://github.com/EnvironmentOntology/envo/wiki/Using-ENVO-with-MIxS">https://github.com/EnvironmentOntology/envo/wiki/Using-ENVO-with-MIxS</a> . Terms from other OBO ontologies are permissible as long as they reference mass/volume nouns (e.g. air, water, blood) and not discrete, countable entities (e.g. a tree, a leaf, a table top)</td>
</tr>
<tr>
<td>food production environmental monitoring zone (<a href="../0001254/">env_monitoring_zone</a>)</td>
<td>An environmental monitoring zone is a formal designation as part of an environmental monitoring program, in which areas of a food production facility are categorized, commonly as zones 1-4, based on likelihood or risk of foodborne pathogen contamination. This field accepts terms listed under food production environmental monitoring zone (<a href="http://purl.obolibrary.org/obo/ENVO">http://purl.obolibrary.org/obo/ENVO</a>). Please add a term to indicate the environmental monitoring zone the sample was taken from</td>
</tr>
<tr>
<td>escalator count (<a href="../0000800/">escalator</a>)</td>
<td>The number of escalators within the built structure</td>
</tr>
<tr>
<td>estimated size (<a href="../0000024/">estimated_size</a>)</td>
<td>The estimated size of the genome prior to sequencing. Of particular importance in the sequencing of (eukaryotic) genome which could remain in draft form for a long or unspecified period</td>
</tr>
<tr>
<td>ethnicity (<a href="../0000895/">ethnicity</a>)</td>
<td>A category of people who identify with each other, usually on the basis of presumed similarities such as a common language, ancestry, history, society, culture, nation or social treatment within their residing area. <a href="https://en.wikipedia.org/wiki/List_of_contemporary_ethnic_groups">https://en.wikipedia.org/wiki/List_of_contemporary_ethnic_groups</a></td>
</tr>
<tr>
<td>ethylbenzene (<a href="../0000155/">ethylbenzene</a>)</td>
<td>Concentration of ethylbenzene in the sample</td>
</tr>
<tr>
<td>exposed ductwork (<a href="../0000144/">exp_duct</a>)</td>
<td>The amount of exposed ductwork in the room</td>
</tr>
<tr>
<td>exposed pipes (<a href="../0000220/">exp_pipe</a>)</td>
<td>The number of exposed pipes in the room</td>
</tr>
<tr>
<td>experimental factor (<a href="../0000008/">experimental_factor</a>)</td>
<td>Variable aspects of an experiment design that can be used to describe an experiment, or set of experiments, in an increasingly detailed manner. This field accepts ontology terms from Experimental Factor Ontology (EFO) and/or Ontology for Biomedical Investigations (OBI)</td>
</tr>
<tr>
<td>exterior door count (<a href="../0000170/">ext_door</a>)</td>
<td>The number of exterior doors in the built structure</td>
</tr>
<tr>
<td>orientations of exterior wall (<a href="../0000817/">ext_wall_orient</a>)</td>
<td>The orientation of the exterior wall</td>
</tr>
<tr>
<td>orientations of exterior window (<a href="../0000818/">ext_window_orient</a>)</td>
<td>The compass direction the exterior window of the room is facing</td>
</tr>
<tr>
<td>extreme weather event (<a href="../0001141/">extr_weather_event</a>)</td>
<td>Unusual weather events that may have affected microbial populations. Multiple terms can be separated by pipes, listed in reverse chronological order</td>
</tr>
<tr>
<td>extrachromosomal elements (<a href="../0000023/">extrachrom_elements</a>)</td>
<td>Do plasmids exist of significant phenotypic consequence (e.g. ones that determine virulence or antibiotic resistance). Megaplasmids? Other plasmids (borrelia has 15+ plasmids)</td>
</tr>
<tr>
<td>history/extreme events (<a href="../0000320/">extreme_event</a>)</td>
<td>Unusual physical events that may have affected microbial populations</td>
</tr>
<tr>
<td>facility type (<a href="../0001252/">facility_type</a>)</td>
<td>Establishment details about the type of facility where the sample was taken. This is independent of the specific product(s) within the facility</td>
</tr>
<tr>
<td>soil_taxonomic/FAO classification (<a href="../0001083/">fao_class</a>)</td>
<td>Soil classification from the FAO World Reference Database for Soil Resources. The list can be found at <a href="http://www.fao.org/nr/land/sols/soil/wrb-soil-maps/reference-groups">http://www.fao.org/nr/land/sols/soil/wrb-soil-maps/reference-groups</a></td>
</tr>
<tr>
<td>farm equipment used (<a href="../0001126/">farm_equip</a>)</td>
<td>List of equipment used for planting, fertilization, harvesting, irrigation, land levelling, residue management, weeding or transplanting during the growing season.  This field accepts terms listed under agricultural implement (<a href="http://purl.obolibrary.org/obo/AGRO_00000416">http://purl.obolibrary.org/obo/AGRO_00000416</a>). Multiple terms can be separated by pipes</td>
</tr>
<tr>
<td>farm equipment sanitization (<a href="../0001124/">farm_equip_san</a>)</td>
<td>Method used to sanitize growing and harvesting equipment. This can including type and concentration of sanitizing solution.  Multiple terms can be separated by one or more pipes</td>
</tr>
<tr>
<td>farm equipment sanitization frequency (<a href="../0001125/">farm_equip_san_freq</a>)</td>
<td>The number of times farm equipment is cleaned. Frequency of cleaning might be on a Daily basis, Weekly, Monthly, Quarterly or Annually</td>
</tr>
<tr>
<td>equipment shared with other farms (<a href="../0001123/">farm_equip_shared</a>)</td>
<td>List of planting, growing or harvesting equipment shared with other farms. This field accepts terms listed under agricultural implement (<a href="http://purl.obolibrary.org/obo/AGRO_00000416">http://purl.obolibrary.org/obo/AGRO_00000416</a>). Multiple terms can be separated by pipes</td>
</tr>
<tr>
<td>farm watering water source (<a href="../0001110/">farm_water_source</a>)</td>
<td>Source of water used on the farm for irrigation of crops or watering of livestock</td>
</tr>
<tr>
<td>feature prediction (<a href="../0000061/">feat_pred</a>)</td>
<td>Method used to predict UViGs features such as ORFs, integration site, etc</td>
</tr>
<tr>
<td>fermentation chemical additives (<a href="../0001185/">ferm_chem_add</a>)</td>
<td>Any chemicals that are added to the fermentation process to achieve the desired final product</td>
</tr>
<tr>
<td>fermentation chemical additives percentage (<a href="../0001186/">ferm_chem_add_perc</a>)</td>
<td>The amount of chemical added to the fermentation process</td>
</tr>
<tr>
<td>fermentation headspace oxygen (<a href="../0001187/">ferm_headspace_oxy</a>)</td>
<td>The amount of headspace oxygen in a fermentation vessel</td>
</tr>
<tr>
<td>fermentation medium (<a href="../0001188/">ferm_medium</a>)</td>
<td>The growth medium used for the fermented food fermentation process, which supplies the required nutrients.  Usually this includes a carbon and nitrogen source, water, micronutrients and chemical additives</td>
</tr>
<tr>
<td>fermentation pH (<a href="../0001189/">ferm_pH</a>)</td>
<td>The pH of the fermented food fermentation process</td>
</tr>
<tr>
<td>fermentation relative humidity (<a href="../0001190/">ferm_rel_humidity</a>)</td>
<td>The relative humidity of the fermented food fermentation process</td>
</tr>
<tr>
<td>fermentation temperature (<a href="../0001191/">ferm_temp</a>)</td>
<td>The temperature of the fermented food fermentation process</td>
</tr>
<tr>
<td>fermentation time (<a href="../0001192/">ferm_time</a>)</td>
<td>The time duration of the fermented food fermentation process</td>
</tr>
<tr>
<td>fermentation vessel (<a href="../0001193/">ferm_vessel</a>)</td>
<td>The type of vessel used for containment of the fermentation</td>
</tr>
<tr>
<td>fertilizer administration (<a href="../0001127/">fertilizer_admin</a>)</td>
<td>Type of fertilizer or amendment added to the soil or water for the purpose of improving substrate health and quality for plant growth. This field accepts terms listed under agronomic fertilizer (<a href="http://purl.obolibrary.org/obo/AGRO_00002062">http://purl.obolibrary.org/obo/AGRO_00002062</a>). Multiple terms may apply and can be separated by pipes, listing in reverse chronological order</td>
</tr>
<tr>
<td>fertilizer administration date (<a href="../0001128/">fertilizer_date</a>)</td>
<td>Date of administration of soil amendment or fertilizer. Multiple terms may apply and can be separated by pipes, listing in reverse chronological order</td>
</tr>
<tr>
<td>fertilizer regimen (<a href="../0000556/">fertilizer_regm</a>)</td>
<td>Information about treatment involving the use of fertilizers; should include the name of fertilizer, amount administered, treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include multiple fertilizer regimens</td>
</tr>
<tr>
<td>field name (<a href="../0000291/">field</a>)</td>
<td>Name of the hydrocarbon field (e.g. Albacora)</td>
</tr>
<tr>
<td>filter type (<a href="../0000765/">filter_type</a>)</td>
<td>A device which removes solid particulates or airborne molecular contaminants</td>
</tr>
<tr>
<td>history/fire (<a href="../0001086/">fire</a>)</td>
<td>Historical and/or physical evidence of fire</td>
</tr>
<tr>
<td>fireplace type (<a href="../0000802/">fireplace_type</a>)</td>
<td>A firebox with chimney</td>
</tr>
<tr>
<td>history/flooding (<a href="../0000319/">flooding</a>)</td>
<td>Historical and/or physical evidence of flooding</td>
</tr>
<tr>
<td>floor age (<a href="../0000164/">floor_age</a>)</td>
<td>The time period since installment of the carpet or flooring</td>
</tr>
<tr>
<td>floor area (<a href="../0000165/">floor_area</a>)</td>
<td>The area of the floor space within the room</td>
</tr>
<tr>
<td>floor condition (<a href="../0000803/">floor_cond</a>)</td>
<td>The physical condition of the floor at the time of sampling; photos or video preferred; use drawings to indicate location of damaged areas</td>
</tr>
<tr>
<td>floor count (<a href="../0000225/">floor_count</a>)</td>
<td>The number of floors in the building, including basements and mechanical penthouse</td>
</tr>
<tr>
<td>floor finish material (<a href="../0000804/">floor_finish_mat</a>)</td>
<td>The floor covering type; the finished surface that is walked on</td>
</tr>
<tr>
<td>floor structure (<a href="../0000806/">floor_struc</a>)</td>
<td>Refers to the structural elements and subfloor upon which the finish flooring is installed</td>
</tr>
<tr>
<td>floor thermal mass (<a href="../0000166/">floor_thermal_mass</a>)</td>
<td>The ability of the floor to provide inertia against temperature fluctuations</td>
</tr>
<tr>
<td>floor signs of water/mold (<a href="../0000805/">floor_water_mold</a>)</td>
<td>Signs of the presence of mold or mildew in a room</td>
</tr>
<tr>
<td>fluorescence (<a href="../0000704/">fluor</a>)</td>
<td>Raw or converted fluorescence of water</td>
</tr>
<tr>
<td>amniotic fluid/foetal health status (<a href="../0000275/">foetal_health_stat</a>)</td>
<td>Specification of foetal health status, should also include abortion</td>
</tr>
<tr>
<td>food additive (<a href="../0001200/">food_additive</a>)</td>
<td>A substance or substances added to food to maintain or improve safety and freshness, to improve or maintain nutritional value, or improve taste, texture and appearance.  This field accepts terms listed under food additive (<a href="http://purl.obolibrary.org/obo/FOODON_03412972">http://purl.obolibrary.org/obo/FOODON_03412972</a>). Multiple terms can be separated by one or more pipes, but please consider limiting this list to the top 5 ingredients listed in order as on the food label.  See also, <a href="https://www.fda.gov/food/food-ingredients-packaging/overview-food-ingredients-additives-colors">https://www.fda.gov/food/food-ingredients-packaging/overview-food-ingredients-additives-colors</a></td>
</tr>
<tr>
<td>food allergen labeling (<a href="../0001201/">food_allergen_label</a>)</td>
<td>A label indication that the product contains a recognized allergen. This field accepts terms listed under dietary claim or use (<a href="http://purl.obolibrary.org/obo/FOODON_03510213">http://purl.obolibrary.org/obo/FOODON_03510213</a>)</td>
</tr>
<tr>
<td>food cleaning process (<a href="../0001182/">food_clean_proc</a>)</td>
<td>The process of cleaning food to separate other environmental materials from the food source. Multiple terms can be separated by pipes</td>
</tr>
<tr>
<td>food contact surface (<a href="../0001131/">food_contact_surf</a>)</td>
<td>The specific container or coating materials in direct contact with the food. Multiple values can be assigned.  This field accepts terms listed under food contact surface (<a href="http://purl.obolibrary.org/obo/FOODON_03500010">http://purl.obolibrary.org/obo/FOODON_03500010</a>)</td>
</tr>
<tr>
<td>food container or wrapping (<a href="../0001132/">food_contain_wrap</a>)</td>
<td>Type of container or wrapping defined by the main container material, the container form, and the material of the liner lids or ends. Also type of container or wrapping by form; prefer description by material first, then by form. This field accepts terms listed under food container or wrapping (<a href="http://purl.obolibrary.org/obo/FOODON_03490100">http://purl.obolibrary.org/obo/FOODON_03490100</a>)</td>
</tr>
<tr>
<td>food cooking process (<a href="../0001202/">food_cooking_proc</a>)</td>
<td>The transformation of raw food by the application of heat. This field accepts terms listed under food cooking (<a href="http://purl.obolibrary.org/obo/FOODON_03450002">http://purl.obolibrary.org/obo/FOODON_03450002</a>)</td>
</tr>
<tr>
<td>food distribution point geographic location (<a href="../0001203/">food_dis_point</a>)</td>
<td>A reference to a place on the Earth, by its name or by its geographical location that refers to a distribution point along the food chain. This field accepts terms listed under geographic location (<a href="http://purl.obolibrary.org/obo/GAZ_00000448">http://purl.obolibrary.org/obo/GAZ_00000448</a>). Reference: Adam Diamond, James Barham. Moving Food Along the Value Chain: Innovations in Regional Food Distribution. U.S. Dept. of Agriculture, Agricultural Marketing Service. Washington, DC. March 2012. <a href="http://dx.doi.org/10.9752/MS045.03-2012">http://dx.doi.org/10.9752/MS045.03-2012</a></td>
</tr>
<tr>
<td>food distribution point geographic location (city) (<a href="../0001204/">food_dis_point_city</a>)</td>
<td>A reference to a place on the Earth, by its name or by its geographical location that refers to a distribution point along the food chain. This field accepts terms listed under geographic location (<a href="http://purl.obolibrary.org/obo/GAZ_00000448">http://purl.obolibrary.org/obo/GAZ_00000448</a>). Reference: Adam Diamond, James Barham. Moving Food Along the Value Chain: Innovations in Regional Food Distribution. U.S. Dept. of Agriculture, Agricultural Marketing Service. Washington, DC. March 2012. <a href="http://dx.doi.org/10.9752/MS045.03-2012">http://dx.doi.org/10.9752/MS045.03-2012</a></td>
</tr>
<tr>
<td>Food harvesting process (<a href="../0001133/">food_harvest_proc</a>)</td>
<td>A harvesting process is a process which takes in some food material from an individual or community of plant or animal organisms in a given context and time, and outputs a precursor or consumable food product. This may include a part of an organism or the whole, and may involve killing the organism</td>
</tr>
<tr>
<td>food ingredient (<a href="../0001205/">food_ingredient</a>)</td>
<td>In this field, please list individual ingredients for multi-component food [FOODON:00002501] and simple foods that is not captured in food_type.  Please use terms that are present in FoodOn.  Multiple terms can be separated by one or more pipes</td>
</tr>
<tr>
<td>food product name legal status (<a href="../0001206/">food_name_status</a>)</td>
<td>A datum indicating that use of a food product name is regulated in some legal jurisdiction. This field accepts terms listed under food product name legal status (<a href="http://purl.obolibrary.org/obo/FOODON_03530087">http://purl.obolibrary.org/obo/FOODON_03530087</a>)</td>
</tr>
<tr>
<td>food product origin geographic location (<a href="../0001207/">food_origin</a>)</td>
<td>A reference to a place on the Earth, by its name or by its geographical location that describes the origin of the food commodity, either in terms of its cultivation or production. This field accepts terms listed under geographic location (<a href="http://purl.obolibrary.org/obo/GAZ_00000448">http://purl.obolibrary.org/obo/GAZ_00000448</a>)</td>
</tr>
<tr>
<td>food package capacity (<a href="../0001208/">food_pack_capacity</a>)</td>
<td>The maximum number of product units within a package</td>
</tr>
<tr>
<td>food packing medium integrity (<a href="../0001209/">food_pack_integrity</a>)</td>
<td>A term label and term id to describe the state of the packing material and text to explain the exact condition.  This field accepts terms listed under food packing medium integrity (<a href="http://purl.obolibrary.org/obo/FOODON_03530218">http://purl.obolibrary.org/obo/FOODON_03530218</a>)</td>
</tr>
<tr>
<td>food packing medium (<a href="../0001134/">food_pack_medium</a>)</td>
<td>The medium in which the food is packed for preservation and handling or the medium surrounding homemade foods, e.g., peaches cooked in sugar syrup. The packing medium may provide a controlled environment for the food. It may also serve to improve palatability and consumer appeal.  This includes edible packing media (e.g. fruit juice), gas other than air (e.g. carbon dioxide), vacuum packed, or packed with aerosol propellant. This field accepts terms under food packing medium (<a href="http://purl.obolibrary.org/obo/FOODON_03480020">http://purl.obolibrary.org/obo/FOODON_03480020</a>). Multiple terms may apply and can be separated by pipes</td>
</tr>
<tr>
<td>food preservation process (<a href="../0001135/">food_preserv_proc</a>)</td>
<td>The methods contributing to the prevention or retardation of microbial, enzymatic or oxidative spoilage and thus to the extension of shelf life. This field accepts terms listed under food preservation process (<a href="http://purl.obolibrary.org/obo/FOODON_03470107">http://purl.obolibrary.org/obo/FOODON_03470107</a>)</td>
</tr>
<tr>
<td>material of contact prior to food packaging (<a href="../0001210/">food_prior_contact</a>)</td>
<td>The material the food contacted (e.g., was processed in) prior to packaging. This field accepts terms listed under material of contact prior to food packaging (<a href="http://purl.obolibrary.org/obo/FOODON_03530077">http://purl.obolibrary.org/obo/FOODON_03530077</a>). If the proper descriptor is not listed please use text to describe the material of contact prior to food packaging</td>
</tr>
<tr>
<td>food production system characteristics (<a href="../0001211/">food_prod</a>)</td>
<td>Descriptors of the food production system or of the agricultural environment and growing conditions related to the farm production system, such as wild caught, organic, free-range, industrial, dairy, beef,  domestic or cultivated food production. This field accepts terms listed under food production (<a href="http://purl.obolibrary.org/obo/FOODON_03530206">http://purl.obolibrary.org/obo/FOODON_03530206</a>). Multiple terms may apply and can be separated by pipes</td>
</tr>
<tr>
<td>food production characteristics (<a href="../0001136/">food_prod_char</a>)</td>
<td>Descriptors of the food production system such as wild caught, free-range, organic, free-range, industrial, dairy, beef</td>
</tr>
<tr>
<td>food product synonym (<a href="../0001212/">food_prod_synonym</a>)</td>
<td>Other names by which the food product is known by (e.g., regional or non-English names)</td>
</tr>
<tr>
<td>food product by quality (<a href="../0001213/">food_product_qual</a>)</td>
<td>Descriptors for describing food visually or via other senses, which is useful for tasks like food inspection where little prior knowledge of how the food came to be is available. Some terms like "food (frozen)" are both a quality descriptor and the output of a process. This field accepts terms listed under food product by quality (<a href="http://purl.obolibrary.org/obo/FOODON_00002454">http://purl.obolibrary.org/obo/FOODON_00002454</a>)</td>
</tr>
<tr>
<td>food product type (<a href="../0001184/">food_product_type</a>)</td>
<td>A food product type is a class of food products that is differentiated by its food composition (e.g., single- or multi-ingredient), processing and/or consumption characteristics. This does not include brand name products but it may include generic food dish categories. This field accepts terms under food product type (<a href="http://purl.obolibrary.org/obo/FOODON:03400361">http://purl.obolibrary.org/obo/FOODON:03400361</a>). For terms related to food product for an animal, consult food product for animal (<a href="http://purl.obolibrary.org/obo/FOODON_03309997">http://purl.obolibrary.org/obo/FOODON_03309997</a>). If the proper descriptor is not listed please use text to describe the food type. Multiple terms can be separated by one or more pipes</td>
</tr>
<tr>
<td>food quality date (<a href="../0001178/">food_quality_date</a>)</td>
<td>The date recommended for the use of the product while at peak quality, this date is not a reflection of safety unless used on infant formula this date is not a reflection of safety and is typically labeled on a food product as "best if used by," best by," "use by," or "freeze by."</td>
</tr>
<tr>
<td>food source (<a href="../0001139/">food_source</a>)</td>
<td>Type of plant or animal from which the food product or its major ingredient is derived or a chemical food source [FDA CFSAN 1995]</td>
</tr>
<tr>
<td>food source age (<a href="../0001251/">food_source_age</a>)</td>
<td>The age of the food source host organim. Depending on the type of host organism, age may be more appropriate to report in days, weeks, or years</td>
</tr>
<tr>
<td>food traceability list category (<a href="../0001214/">food_trace_list</a>)</td>
<td>The FDA is proposing to establish additional traceability recordkeeping requirements (beyond what is already required in existing regulations) for persons who manufacture, process, pack, or hold foods the Agency has designated for inclusion on the Food Traceability List. The Food Traceability List (FTL) identifies the foods for which the additional traceability records described in the proposed rule would be required. The term  Food Traceability List  (FTL) refers not only to the foods specifically listed (<a href="https://www.fda.gov/media/142303/download">https://www.fda.gov/media/142303/download</a>), but also to any foods that contain listed foods as ingredients</td>
</tr>
<tr>
<td>food shipping transportation method (<a href="../0001137/">food_trav_mode</a>)</td>
<td>A descriptor for the method of movement of food commodity along the food distribution system.  This field accepts terms listed under travel mode (<a href="http://purl.obolibrary.org/obo/GENEPIO_0001064">http://purl.obolibrary.org/obo/GENEPIO_0001064</a>). If the proper descrptor is not listed please use text to describe the mode of travel. Multiple terms can be separated by one or more pipes</td>
</tr>
<tr>
<td>food shipping transportation vehicle (<a href="../0001138/">food_trav_vehic</a>)</td>
<td>A descriptor for the mobile machine which is used to transport food commodities along the food distribution system.  This field accepts terms listed under vehicle (<a href="http://purl.obolibrary.org/obo/ENVO_01000604">http://purl.obolibrary.org/obo/ENVO_01000604</a>). If the proper descrptor is not listed please use text to describe the mode of travel. Multiple terms can be separated by one or more pipes</td>
</tr>
<tr>
<td>food treatment process (<a href="../0001140/">food_treat_proc</a>)</td>
<td>Used to specifically characterize a food product based on the treatment or processes applied to the product or any indexed ingredient. The processes include adding, substituting or removing components or modifying the food or component, e.g., through fermentation. Multiple values can be assigned. This fields accepts terms listed under food treatment process (<a href="http://purl.obolibrary.org/obo/FOODON_03460111">http://purl.obolibrary.org/obo/FOODON_03460111</a>)</td>
</tr>
<tr>
<td>frequency of cleaning (<a href="../0000226/">freq_clean</a>)</td>
<td>The number of times the sample location is cleaned. Frequency of cleaning might be on a Daily basis, Weekly, Monthly, Quarterly or Annually</td>
</tr>
<tr>
<td>frequency of cooking (<a href="../0000227/">freq_cook</a>)</td>
<td>The number of times a meal is cooked per week</td>
</tr>
<tr>
<td>fungicide regimen (<a href="../0000557/">fungicide_regm</a>)</td>
<td>Information about treatment involving use of fungicides; should include the name of fungicide, amount administered, treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include multiple fungicide regimens</td>
</tr>
<tr>
<td>furniture (<a href="../0000807/">furniture</a>)</td>
<td>The types of furniture present in the sampled room</td>
</tr>
<tr>
<td>gaseous environment (<a href="../0000558/">gaseous_environment</a>)</td>
<td>Use of conditions with differing gaseous environments; should include the name of gaseous compound, amount administered, treatment duration, interval and total experimental duration; can include multiple gaseous environment regimens</td>
</tr>
<tr>
<td>gaseous substances (<a href="../0000661/">gaseous_substances</a>)</td>
<td>Amount or concentration of substances such as hydrogen sulfide, carbon dioxide, methane, etc.; can include multiple substances</td>
</tr>
<tr>
<td>gastrointestinal tract disorder (<a href="../0000280/">gastrointest_disord</a>)</td>
<td>History of gastrointestinal tract disorders; can include multiple disorders. History of blood disorders; can include multiple disorders.  The terms should be chosen from the DO (Human Disease Ontology) at <a href="http://www.disease-ontology.org">http://www.disease-ontology.org</a>, gastrointestinal system disease (<a href="https://disease-ontology.org/?id=DOID:77">https://disease-ontology.org/?id=DOID:77</a>)</td>
</tr>
<tr>
<td>gender of restroom (<a href="../0000808/">gender_restroom</a>)</td>
<td>The gender type of the restroom</td>
</tr>
<tr>
<td>genetic modification (<a href="../0000859/">genetic_mod</a>)</td>
<td>Genetic modifications of the genome of an organism, which may occur naturally by spontaneous mutation, or be introduced by some experimental means, e.g. specification of a transgene or the gene knocked-out or details of transient transfection</td>
</tr>
<tr>
<td>geographic location (country and/or sea,region) (<a href="../0000010/">geo_loc_name</a>)</td>
<td>The geographical origin of the sample as defined by the country or sea name followed by specific region name. Country or sea names should be chosen from the INSDC country list (<a href="http://insdc.org/country.html">http://insdc.org/country.html</a>), or the GAZ ontology (<a href="http://purl.bioontology.org/ontology/GAZ">http://purl.bioontology.org/ontology/GAZ</a>)</td>
</tr>
<tr>
<td>amniotic fluid/gestation state (<a href="../0000272/">gestation_state</a>)</td>
<td>Specification of the gestation state</td>
</tr>
<tr>
<td>glucosidase activity (<a href="../0000137/">glucosidase_act</a>)</td>
<td>Measurement of glucosidase activity</td>
</tr>
<tr>
<td>gravidity (<a href="../0000875/">gravidity</a>)</td>
<td>Whether or not subject is gravid, and if yes date due or date post-conception, specifying which is used</td>
</tr>
<tr>
<td>gravity (<a href="../0000559/">gravity</a>)</td>
<td>Information about treatment involving use of gravity factor to study various types of responses in presence, absence or modified levels of gravity; treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include multiple treatments</td>
</tr>
<tr>
<td>growth facility (<a href="../0001043/">growth_facil</a>)</td>
<td>Type of facility where the sampled plant was grown; controlled vocabulary: growth chamber, open top chamber, glasshouse, experimental garden, field. Alternatively use Crop Ontology (CO) terms, see <a href="http://www.cropontology.org/ontology/CO_715/Crop%20Research">http://www.cropontology.org/ontology/CO_715/Crop%20Research</a></td>
</tr>
<tr>
<td>growth habit (<a href="../0001044/">growth_habit</a>)</td>
<td>Characteristic shape, appearance or growth form of a plant species</td>
</tr>
<tr>
<td>growth hormone regimen (<a href="../0000560/">growth_hormone_regm</a>)</td>
<td>Information about treatment involving use of growth hormones; should include the name of growth hormone, amount administered, treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include multiple growth hormone regimens</td>
</tr>
<tr>
<td>growth medium (<a href="../0001108/">growth_medium</a>)</td>
<td>A liquid or gel containing nutrients, salts, and other factors formulated to support the growth of microorganisms, cells, or plants (National Cancer Institute Thesaurus).  The name of the medium used to grow the microorganism</td>
</tr>
<tr>
<td>gynecological disorder (<a href="../0000288/">gynecologic_disord</a>)</td>
<td>History of gynecological disorders; can include multiple disorders. The terms should be chosen from the DO (Human Disease Ontology) at <a href="http://www.disease-ontology.org">http://www.disease-ontology.org</a>, female reproductive system disease (<a href="https://disease-ontology.org/?id=DOID:229">https://disease-ontology.org/?id=DOID:229</a>)</td>
</tr>
<tr>
<td>hallway/corridor count (<a href="../0000228/">hall_count</a>)</td>
<td>The total count of hallways and cooridors in the built structure</td>
</tr>
<tr>
<td>handidness (<a href="../0000809/">handidness</a>)</td>
<td>The handidness of the individual sampled</td>
</tr>
<tr>
<td>hydrocarbon type produced (<a href="../0000989/">hc_produced</a>)</td>
<td>Main hydrocarbon type produced from resource (i.e. Oil, gas, condensate, etc). If "other" is specified, please propose entry in "additional info" field</td>
</tr>
<tr>
<td>hydrocarbon resource type (<a href="../0000988/">hcr</a>)</td>
<td>Main Hydrocarbon Resource type. The term "Hydrocarbon Resource" HCR defined as a natural environmental feature containing large amounts of hydrocarbons at high concentrations potentially suitable for commercial exploitation. This term should not be confused with the Hydrocarbon Occurrence term which also includes hydrocarbon-rich environments with currently limited commercial interest such as seeps, outcrops, gas hydrates etc. If "other" is specified, please propose entry in "additional info" field</td>
</tr>
<tr>
<td>formation water salinity (<a href="../0000406/">hcr_fw_salinity</a>)</td>
<td>Original formation water salinity (prior to secondary recovery e.g. Waterflooding) expressed as TDS</td>
</tr>
<tr>
<td>hydrocarbon resource geological age (<a href="../0000993/">hcr_geol_age</a>)</td>
<td>Geological age of hydrocarbon resource (Additional info: <a href="https://en.wikipedia.org/wiki/Period_(geology">https://en.wikipedia.org/wiki/Period_(geology</a>)). If "other" is specified, please propose entry in "additional info" field</td>
</tr>
<tr>
<td>hydrocarbon resource original pressure (<a href="../0000395/">hcr_pressure</a>)</td>
<td>Original pressure of the hydrocarbon resource</td>
</tr>
<tr>
<td>hydrocarbon resource original temperature (<a href="../0000393/">hcr_temp</a>)</td>
<td>Original temperature of the hydrocarbon resource</td>
</tr>
<tr>
<td>heating and cooling system type (<a href="../0000766/">heat_cool_type</a>)</td>
<td>Methods of conditioning or heating a room or building</td>
</tr>
<tr>
<td>heating delivery locations (<a href="../0000810/">heat_deliv_loc</a>)</td>
<td>The location of heat delivery within the room</td>
</tr>
<tr>
<td>heating system delivery method (<a href="../0000812/">heat_sys_deliv_meth</a>)</td>
<td>The method by which the heat is delivered through the system</td>
</tr>
<tr>
<td>heating system identifier (<a href="../0000833/">heat_system_id</a>)</td>
<td>The heating system identifier</td>
</tr>
<tr>
<td>extreme_unusual_properties/heavy metals (<a href="../0000652/">heavy_metals</a>)</td>
<td>Heavy metals present in the sequenced sample and their concentrations. For multiple heavy metals and concentrations, add multiple copies of this field</td>
</tr>
<tr>
<td>extreme_unusual_properties/heavy metals method (<a href="../0000343/">heavy_metals_meth</a>)</td>
<td>Reference or method used in determining heavy metals</td>
</tr>
<tr>
<td>height carpet fiber mat (<a href="../0000167/">height_carper_fiber</a>)</td>
<td>The average carpet fiber height in the indoor environment</td>
</tr>
<tr>
<td>herbicide regimen (<a href="../0000561/">herbicide_regm</a>)</td>
<td>Information about treatment involving use of herbicides; information about treatment involving use of growth hormones; should include the name of herbicide, amount administered, treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include multiple regimens</td>
</tr>
<tr>
<td>horizon method (<a href="../0000321/">horizon_meth</a>)</td>
<td>Reference or method used in determining the horizon</td>
</tr>
<tr>
<td>host age (<a href="../0000255/">host_age</a>)</td>
<td>Age of host at the time of sampling; relevant scale depends on species and study, e.g. Could be seconds for amoebae or centuries for trees</td>
</tr>
<tr>
<td>host body habitat (<a href="../0000866/">host_body_habitat</a>)</td>
<td>Original body habitat where the sample was obtained from</td>
</tr>
<tr>
<td>host body-mass index (<a href="../0000317/">host_body_mass_index</a>)</td>
<td>Body mass index, calculated as weight/(height)squared</td>
</tr>
<tr>
<td>host body product (<a href="../0000888/">host_body_product</a>)</td>
<td>Substance produced by the body, e.g. Stool, mucus, where the sample was obtained from. Use terms from the foundational model of anatomy ontology (fma) or Uber-anatomy ontology (UBERON)</td>
</tr>
<tr>
<td>host body site (<a href="../0000867/">host_body_site</a>)</td>
<td>Name of body site where the sample was obtained from, such as a specific organ or tissue (tongue, lung etc...). Use terms from the foundational model of anatomy ontology (fma) or the Uber-anatomy ontology (UBERON)</td>
</tr>
<tr>
<td>host body temperature (<a href="../0000274/">host_body_temp</a>)</td>
<td>Core body temperature of the host when sample was collected</td>
</tr>
<tr>
<td>host cellular location (<a href="../0001313/">host_cellular_loc</a>)</td>
<td>The localization of the symbiotic host organism within the host from which it was sampled: e.g. intracellular if the symbiotic host organism is localized within the cells or extracellular if the symbiotic host organism is localized outside of cells</td>
</tr>
<tr>
<td>host color (<a href="../0000260/">host_color</a>)</td>
<td>The color of host</td>
</tr>
<tr>
<td>host common name (<a href="../0000248/">host_common_name</a>)</td>
<td>Common name of the host</td>
</tr>
<tr>
<td>host dependence (<a href="../0001315/">host_dependence</a>)</td>
<td>Type of host dependence for the symbiotic host organism to its host</td>
</tr>
<tr>
<td>host diet (<a href="../0000869/">host_diet</a>)</td>
<td>Type of diet depending on the host, for animals omnivore, herbivore etc., for humans high-fat, meditteranean etc.; can include multiple diet types</td>
</tr>
<tr>
<td>host disease status (<a href="../0000031/">host_disease_stat</a>)</td>
<td>List of diseases with which the host has been diagnosed; can include multiple diagnoses. The value of the field depends on host; for humans the terms should be chosen from the DO (Human Disease Ontology) at <a href="https://www.disease-ontology.org">https://www.disease-ontology.org</a>, non-human host diseases are free text</td>
</tr>
<tr>
<td>host dry mass (<a href="../0000257/">host_dry_mass</a>)</td>
<td>Measurement of dry mass</td>
</tr>
<tr>
<td>host family relationship (<a href="../0000872/">host_fam_rel</a>)</td>
<td>Relationships to other hosts in the same study; can include multiple relationships</td>
</tr>
<tr>
<td>host genotype (<a href="../0000365/">host_genotype</a>)</td>
<td>Observed genotype</td>
</tr>
<tr>
<td>host growth conditions (<a href="../0000871/">host_growth_cond</a>)</td>
<td>Literature reference giving growth conditions of the host</td>
</tr>
<tr>
<td>host height (<a href="../0000264/">host_height</a>)</td>
<td>The height of subject</td>
</tr>
<tr>
<td>host HIV status (<a href="../0000265/">host_hiv_stat</a>)</td>
<td>HIV status of subject, if yes HAART initiation status should also be indicated as [YES or NO]</td>
</tr>
<tr>
<td>host infra-specific name (<a href="../0000253/">host_infra_spec_name</a>)</td>
<td>Taxonomic information about the host below subspecies level</td>
</tr>
<tr>
<td>host infra-specific rank (<a href="../0000254/">host_infra_spec_rank</a>)</td>
<td>Taxonomic rank information about the host below subspecies level, such as variety, form, rank etc</td>
</tr>
<tr>
<td>host last meal (<a href="../0000870/">host_last_meal</a>)</td>
<td>Content of last meal and time since feeding; can include multiple values</td>
</tr>
<tr>
<td>host length (<a href="../0000256/">host_length</a>)</td>
<td>The length of subject</td>
</tr>
<tr>
<td>host life stage (<a href="../0000251/">host_life_stage</a>)</td>
<td>Description of life stage of host</td>
</tr>
<tr>
<td>host number individual (<a href="../0001305/">host_number</a>)</td>
<td>Number of symbiotic host individuals pooled at the time of collection</td>
</tr>
<tr>
<td>host occupation (<a href="../0000896/">host_occupation</a>)</td>
<td>Most frequent job performed by subject</td>
</tr>
<tr>
<td>observed coinfecting organisms in host of host (<a href="../0001310/">host_of_host_coinf</a>)</td>
<td>The taxonomic name of any coinfecting organism observed in a symbiotic relationship with the host of the sampled host organism. e.g. where a sample collected from a host trematode species (A) which was collected from a host_of_host fish (B) that was also infected with a nematode (C), the value here would be (C) the nematode {species name} or {common name}. Multiple co-infecting species may be added in a comma-separated list. For listing symbiotic organisms associated with the host (A) use the term Observed host symbiont</td>
</tr>
<tr>
<td>host of the symbiotic host disease status (<a href="../0001319/">host_of_host_disease</a>)</td>
<td>List of diseases with which the host of the symbiotic host organism has been diagnosed; can include multiple diagnoses. The value of the field depends on host; for humans the terms should be chosen from the DO (Human Disease Ontology) at <a href="https://www.disease-ontology.org">https://www.disease-ontology.org</a>, non-human host diseases are free text</td>
</tr>
<tr>
<td>host of the symbiotic host local environmental context (<a href="../0001325/">host_of_host_env_loc</a>)</td>
<td>For a symbiotic host organism the local anatomical environment within its host may have causal influences. Report the anatomical entity(s) which are in the direct environment of the symbiotic host organism being sampled and which you believe have significant causal influences on your sample or specimen. For example, if the symbiotic host organism being sampled is an intestinal worm, its local environmental context will be the term for intestine from UBERON (<a href="http://uberon.github.io/">http://uberon.github.io/</a>)</td>
</tr>
<tr>
<td>host of the symbiotic host environemental medium (<a href="../0001326/">host_of_host_env_med</a>)</td>
<td>Report the environmental material(s) immediately surrounding the symbiotic host organism at the time of sampling. This usually will be a tissue or substance type from the host, but may be another material if the symbiont is external to the host. We recommend using classes from the UBERON ontology, but subclasses of 'environmental material' (<a href="http://purl.obolibrary.org/obo/ENVO_00010483">http://purl.obolibrary.org/obo/ENVO_00010483</a>) may also be used. EnvO documentation about how to use the field: <a href="https://github.com/EnvironmentOntology/envo/wiki/Using-ENVO-with-MIxS">https://github.com/EnvironmentOntology/envo/wiki/Using-ENVO-with-MIxS</a> . Terms from other OBO ontologies are permissible as long as they reference mass/volume nouns (e.g. air, water, blood) and not discrete, countable entities (e.g. intestines, heart).MIxS . Terms from other OBO ontologies are permissible as long as they reference mass/volume nouns (e.g. air, water, blood) and not discrete, countable entities (e.g. intestines, heart)</td>
</tr>
<tr>
<td>host of the symbiotic host family relationship (<a href="../0001328/">host_of_host_fam_rel</a>)</td>
<td>Familial relationship of the host of the symbiotic host organisms to other hosts of symbiotic host organism in the same study; can include multiple relationships</td>
</tr>
<tr>
<td>host of the symbiotic host genotype (<a href="../0001331/">host_of_host_geno</a>)</td>
<td>Observed genotype of the host of the symbiotic host organism</td>
</tr>
<tr>
<td>host of the symbiotic host gravidity (<a href="../0001333/">host_of_host_gravid</a>)</td>
<td>Whether or not the host of the symbiotic host organism is gravid, and if yes date due or date post-conception, specifying which is used</td>
</tr>
<tr>
<td>host of the symbiotic host infra-specific name (<a href="../0001329/">host_of_host_infname</a>)</td>
<td>Taxonomic name information of the host of the symbiotic host organism below subspecies level</td>
</tr>
<tr>
<td>host of the symbiotic host infra-specific rank (<a href="../0001330/">host_of_host_infrank</a>)</td>
<td>Taxonomic rank information about the host of the symbiotic host organism below subspecies level, such as variety, form, rank etc</td>
</tr>
<tr>
<td>host of the symbiotic host common name (<a href="../0001324/">host_of_host_name</a>)</td>
<td>Common name of the host of the symbiotic host organism</td>
</tr>
<tr>
<td>host of the symbiotic host phenotype (<a href="../0001332/">host_of_host_pheno</a>)</td>
<td>Phenotype of the host of the symbiotic host organism. For phenotypic quality ontology (PATO) terms, see <a href="http://purl.bioontology.org/ontology/pato">http://purl.bioontology.org/ontology/pato</a></td>
</tr>
<tr>
<td>host of the symbiotic host subject id (<a href="../0001327/">host_of_host_sub_id</a>)</td>
<td>A unique identifier by which each host of the symbiotic host organism subject can be referred to, de-identified, e.g. #H14</td>
</tr>
<tr>
<td>host of the symbiotic host taxon id (<a href="../0001306/">host_of_host_taxid</a>)</td>
<td>NCBI taxon id of the host of the symbiotic host organism</td>
</tr>
<tr>
<td>host of the symbiotic host total mass (<a href="../0001334/">host_of_host_totmass</a>)</td>
<td>Total mass of the host of the symbiotic host organism at collection, the unit depends on the host</td>
</tr>
<tr>
<td>host phenotype (<a href="../0000874/">host_phenotype</a>)</td>
<td>Phenotype of human or other host. Use terms from the phenotypic quality ontology (pato) or the Human Phenotype Ontology (HP)</td>
</tr>
<tr>
<td>host prediction approach (<a href="../0000088/">host_pred_appr</a>)</td>
<td>Tool or approach used for host prediction</td>
</tr>
<tr>
<td>host prediction estimated accuracy (<a href="../0000089/">host_pred_est_acc</a>)</td>
<td>For each tool or approach used for host prediction, estimated false discovery rates should be included, either computed de novo or from the literature</td>
</tr>
<tr>
<td>host pulse (<a href="../0000333/">host_pulse</a>)</td>
<td>Resting pulse, measured as beats per minute</td>
</tr>
<tr>
<td>host sex (<a href="../0000811/">host_sex</a>)</td>
<td>Gender or physical sex of the host</td>
</tr>
<tr>
<td>host shape (<a href="../0000261/">host_shape</a>)</td>
<td>Morphological shape of host</td>
</tr>
<tr>
<td>host specificity or range (<a href="../0000030/">host_spec_range</a>)</td>
<td>The range and diversity of host species that an organism is capable of infecting, defined by NCBI taxonomy identifier</td>
</tr>
<tr>
<td>host specificity (<a href="../0001308/">host_specificity</a>)</td>
<td>Level of specificity of symbiont-host interaction: e.g. generalist (symbiont able to establish associations with distantly related hosts) or species-specific</td>
</tr>
<tr>
<td>host subject id (<a href="../0000861/">host_subject_id</a>)</td>
<td>A unique identifier by which each subject can be referred to, de-identified</td>
</tr>
<tr>
<td>host subspecific genetic lineage (<a href="../0001318/">host_subspecf_genlin</a>)</td>
<td>Information about the genetic distinctness of the host organism below the subspecies level e.g., serovar, serotype, biotype, ecotype, variety, cultivar, or any relevant genetic typing schemes like Group I plasmid. Subspecies should not be recorded in this term, but in the NCBI taxonomy. Supply both the lineage name and the lineage rank separated by a colon, e.g., biovar:abc123</td>
</tr>
<tr>
<td>host substrate (<a href="../0000252/">host_substrate</a>)</td>
<td>The growth substrate of the host</td>
</tr>
<tr>
<td>observed host symbionts (<a href="../0001298/">host_symbiont</a>)</td>
<td>The taxonomic name of the organism(s) found living in mutualistic, commensalistic, or parasitic symbiosis with the specific host. The sampled symbiont can have its own symbionts. For example, parasites may have hyperparasites (=parasites of the parasite)</td>
</tr>
<tr>
<td>host taxid (<a href="../0000250/">host_taxid</a>)</td>
<td>NCBI taxon id of the host, e.g. 9606</td>
</tr>
<tr>
<td>host total mass (<a href="../0000263/">host_tot_mass</a>)</td>
<td>Total mass of the host at collection, the unit depends on host</td>
</tr>
<tr>
<td>host wet mass (<a href="../0000567/">host_wet_mass</a>)</td>
<td>Measurement of wet mass</td>
</tr>
<tr>
<td>HRT (<a href="../0000969/">hrt</a>)</td>
<td>Whether subject had hormone replacement theraphy, and if yes start date</td>
</tr>
<tr>
<td>humidity (<a href="../0000100/">humidity</a>)</td>
<td>Amount of water vapour in the air, at the time of sampling</td>
</tr>
<tr>
<td>humidity regimen (<a href="../0000568/">humidity_regm</a>)</td>
<td>Information about treatment involving an exposure to varying degree of humidity; information about treatment involving use of growth hormones; should include amount of humidity administered, treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include multiple regimens</td>
</tr>
<tr>
<td>hygienic food production area (<a href="../0001253/">hygienic_area</a>)</td>
<td>The subdivision of areas within a food production facility according to hygienic requirements. This field accepts terms listed under hygienic food production area (<a href="http://purl.obolibrary.org/obo/ENVO">http://purl.obolibrary.org/obo/ENVO</a>). Please add a term that most accurately indicates the hygienic area your sample was taken from according to the definitions provided</td>
</tr>
<tr>
<td>hysterectomy (<a href="../0000287/">hysterectomy</a>)</td>
<td>Specification of whether hysterectomy was performed</td>
</tr>
<tr>
<td>IHMC medication code (<a href="../0000884/">ihmc_medication_code</a>)</td>
<td>Can include multiple medication codes</td>
</tr>
<tr>
<td>indoor space (<a href="../0000763/">indoor_space</a>)</td>
<td>A distinguishable space within a structure, the purpose for which discrete areas of a building is used</td>
</tr>
<tr>
<td>indoor surface (<a href="../0000764/">indoor_surf</a>)</td>
<td>Type of indoor surface</td>
</tr>
<tr>
<td>industrial effluent percent (<a href="../0000662/">indust_eff_percent</a>)</td>
<td>Percentage of industrial effluents received by wastewater treatment plant</td>
</tr>
<tr>
<td>inorganic particles (<a href="../0000664/">inorg_particles</a>)</td>
<td>Concentration of particles such as sand, grit, metal particles, ceramics, etc.; can include multiple particles</td>
</tr>
<tr>
<td>inside lux light (<a href="../0000168/">inside_lux</a>)</td>
<td>The recorded value at sampling time (power density)</td>
</tr>
<tr>
<td>interior wall condition (<a href="../0000813/">int_wall_cond</a>)</td>
<td>The physical condition of the wall at the time of sampling; photos or video preferred; use drawings to indicate location of damaged areas</td>
</tr>
<tr>
<td>intended consumer (<a href="../0001144/">intended_consumer</a>)</td>
<td>Food consumer type, human or animal, for which the food product is produced and marketed. This field accepts terms listed under food consumer group (<a href="http://purl.obolibrary.org/obo/FOODON_03510136">http://purl.obolibrary.org/obo/FOODON_03510136</a>) or NCBI taxid</td>
</tr>
<tr>
<td>isolation and growth condition (<a href="../0000003/">isol_growth_condt</a>)</td>
<td>Publication reference in the form of pubmed ID (pmid), digital object identifier (doi) or url for isolation and growth condition specifications of the organism/material</td>
</tr>
<tr>
<td>injection water breakthrough date of specific well (<a href="../0001010/">iw_bt_date_well</a>)</td>
<td>Injection water breakthrough date per well following a secondary and/or tertiary recovery</td>
</tr>
<tr>
<td>injection water fraction (<a href="../0000455/">iwf</a>)</td>
<td>Proportion of the produced fluids derived from injected water at the time of sampling. (e.g. 87%)</td>
</tr>
<tr>
<td>urine/kidney disorder (<a href="../0000277/">kidney_disord</a>)</td>
<td>History of kidney disorders; can include multiple disorders. The terms should be chosen from the DO (Human Disease Ontology) at <a href="http://www.disease-ontology.org">http://www.disease-ontology.org</a>, kidney disease (<a href="https://disease-ontology.org/?id=DOID:557">https://disease-ontology.org/?id=DOID:557</a>)</td>
</tr>
<tr>
<td>last time swept/mopped/vacuumed (<a href="../0000814/">last_clean</a>)</td>
<td>The last time the floor was cleaned (swept, mopped, vacuumed)</td>
</tr>
<tr>
<td>geographic location (latitude and longitude) (<a href="../0000009/">lat_lon</a>)</td>
<td>The geographical origin of the sample as defined by latitude and longitude. The values should be reported in decimal degrees and in WGS84 system</td>
</tr>
<tr>
<td>library layout (<a href="../0000041/">lib_layout</a>)</td>
<td>Specify whether to expect single, paired, or other configuration of reads</td>
</tr>
<tr>
<td>library reads sequenced (<a href="../0000040/">lib_reads_seqd</a>)</td>
<td>Total number of clones sequenced from the library</td>
</tr>
<tr>
<td>library screening strategy (<a href="../0000043/">lib_screen</a>)</td>
<td>Specific enrichment or screening methods applied before and/or after creating libraries</td>
</tr>
<tr>
<td>library size (<a href="../0000039/">lib_size</a>)</td>
<td>Total number of clones in the library prepared for the project</td>
</tr>
<tr>
<td>library vector (<a href="../0000042/">lib_vector</a>)</td>
<td>Cloning vector type(s) used in construction of libraries</td>
</tr>
<tr>
<td>library preparation kit (<a href="../0001145/">library_prep_kit</a>)</td>
<td>Packaged kits (containing adapters, indexes, enzymes, buffers etc.), tailored for specific sequencing workflows, which allow the simplified preparation of sequencing-ready libraries for small genomes, amplicons, and plasmids</td>
</tr>
<tr>
<td>light intensity (<a href="../0000706/">light_intensity</a>)</td>
<td>Measurement of light intensity</td>
</tr>
<tr>
<td>light regimen (<a href="../0000569/">light_regm</a>)</td>
<td>Information about treatment(s) involving exposure to light, including both light intensity and quality</td>
</tr>
<tr>
<td>light type (<a href="../0000769/">light_type</a>)</td>
<td>Application of light to achieve some practical or aesthetic effect. Lighting includes the use of both artificial light sources such as lamps and light fixtures, as well as natural illumination by capturing daylight. Can also include absence of light</td>
</tr>
<tr>
<td>links to additional analysis (<a href="../0000340/">link_addit_analys</a>)</td>
<td>Link to additional analysis results performed on the sample</td>
</tr>
<tr>
<td>link to classification information (<a href="../0000329/">link_class_info</a>)</td>
<td>Link to digitized soil maps or other soil classification information</td>
</tr>
<tr>
<td>link to climate information (<a href="../0000328/">link_climate_info</a>)</td>
<td>Link to climate resource</td>
</tr>
<tr>
<td>lithology (<a href="../0000990/">lithology</a>)</td>
<td>Hydrocarbon resource main lithology (Additional information: <a href="http://petrowiki.org/Lithology_and_rock_type_determination">http://petrowiki.org/Lithology_and_rock_type_determination</a>). If "other" is specified, please propose entry in "additional info" field</td>
</tr>
<tr>
<td>liver disorder (<a href="../0000282/">liver_disord</a>)</td>
<td>History of liver disorders; can include multiple disorders. The terms should be chosen from the DO (Human Disease Ontology) at <a href="http://www.disease-ontology.org">http://www.disease-ontology.org</a>, liver disease (<a href="https://disease-ontology.org/?id=DOID:409">https://disease-ontology.org/?id=DOID:409</a>)</td>
</tr>
<tr>
<td>soil_taxonomic/local classification (<a href="../0000330/">local_class</a>)</td>
<td>Soil classification based on local soil classification system</td>
</tr>
<tr>
<td>soil_taxonomic/local classification method (<a href="../0000331/">local_class_meth</a>)</td>
<td>Reference or method used in determining the local soil classification</td>
</tr>
<tr>
<td>lot number (<a href="../0001147/">lot_number</a>)</td>
<td>A distinctive alpha-numeric identification code assigned by the manufacturer or distributor to a specific quantity of manufactured material or product within a batch. Synonym: Batch Number.  The submitter should provide lot number of the item followed by the item name for which the lot number was provided</td>
</tr>
<tr>
<td>MAG coverage software (<a href="../0000080/">mag_cov_software</a>)</td>
<td>Tool(s) used to determine the genome coverage if coverage is used as a binning parameter in the extraction of genomes from metagenomic datasets</td>
</tr>
<tr>
<td>magnesium (<a href="../0000431/">magnesium</a>)</td>
<td>Concentration of magnesium in the sample</td>
</tr>
<tr>
<td>amniotic fluid/maternal health status (<a href="../0000273/">maternal_health_stat</a>)</td>
<td>Specification of the maternal health status</td>
</tr>
<tr>
<td>maximum occupancy (<a href="../0000229/">max_occup</a>)</td>
<td>The maximum amount of people allowed in the indoor environment</td>
</tr>
<tr>
<td>mean friction velocity (<a href="../0000498/">mean_frict_vel</a>)</td>
<td>Measurement of mean friction velocity</td>
</tr>
<tr>
<td>mean peak friction velocity (<a href="../0000502/">mean_peak_frict_vel</a>)</td>
<td>Measurement of mean peak friction velocity</td>
</tr>
<tr>
<td>mechanical structure (<a href="../0000815/">mech_struc</a>)</td>
<td>mechanical structure: a moving structure</td>
</tr>
<tr>
<td>mechanical damage (<a href="../0001052/">mechanical_damage</a>)</td>
<td>Information about any mechanical damage exerted on the plant; can include multiple damages and sites</td>
</tr>
<tr>
<td>medical history performed (<a href="../0000897/">medic_hist_perform</a>)</td>
<td>Whether full medical history was collected</td>
</tr>
<tr>
<td>menarche (<a href="../0000965/">menarche</a>)</td>
<td>Date of most recent menstruation</td>
</tr>
<tr>
<td>menopause (<a href="../0000968/">menopause</a>)</td>
<td>Date of onset of menopause</td>
</tr>
<tr>
<td>methane (<a href="../0000101/">methane</a>)</td>
<td>Methane (gas) amount or concentration at the time of sampling</td>
</tr>
<tr>
<td>microbial biomass method (<a href="../0000339/">micro_biomass_meth</a>)</td>
<td>Reference or method used in determining microbial biomass</td>
</tr>
<tr>
<td>microbiological culture medium (<a href="../0001216/">microb_cult_med</a>)</td>
<td>A culture medium used to select for, grow, and maintain prokaryotic microorganisms. Can be in either liquid (broth) or solidified (e.g. with agar) forms. This field accepts terms listed under microbiological culture medium (<a href="http://purl.obolibrary.org/obo/MICRO_0000067">http://purl.obolibrary.org/obo/MICRO_0000067</a>). If the proper descriptor is not listed please use text to describe the culture medium</td>
</tr>
<tr>
<td>microbial starter (<a href="../0001217/">microb_start</a>)</td>
<td>Any type of microorganisms used in food production.  This field accepts terms listed under live organisms for food production (<a href="http://purl.obolibrary.org/obo/FOODON_0344453">http://purl.obolibrary.org/obo/FOODON_0344453</a>)</td>
</tr>
<tr>
<td>microbial starter organism count (<a href="../0001218/">microb_start_count</a>)</td>
<td>Total cell count of starter culture per gram, volume or area of sample and the method that was used for the enumeration (e.g. qPCR, atp, mpn, etc.) should also be provided. (example : total prokaryotes; 3.5e7 cells per ml; qPCR)</td>
</tr>
<tr>
<td>microbial starter inoculation (<a href="../0001219/">microb_start_inoc</a>)</td>
<td>The amount of starter culture used to inoculate a new batch</td>
</tr>
<tr>
<td>microbial starter preparation (<a href="../0001220/">microb_start_prep</a>)</td>
<td>Information about the protocol or method used to prepare the starter inoculum</td>
</tr>
<tr>
<td>microbial starter source (<a href="../0001221/">microb_start_source</a>)</td>
<td>The source from which the microbial starter culture was sourced.  If commercially supplied, list supplier</td>
</tr>
<tr>
<td>microbial starter NCBI taxonomy ID (<a href="../0001222/">microb_start_taxID</a>)</td>
<td>Please include Genus species and strain ID, if known of microorganisms used in food production. For complex communities, pipes can be used to separate two or more microbes</td>
</tr>
<tr>
<td>microbial biomass (<a href="../0000650/">microbial_biomass</a>)</td>
<td>The part of the organic matter in the soil that constitutes living microorganisms smaller than 5-10 micrometer. If you keep this, you would need to have correction factors used for conversion to the final units</td>
</tr>
<tr>
<td>multiplex identifiers (<a href="../0000047/">mid</a>)</td>
<td>Molecular barcodes, called Multiplex Identifiers (MIDs), that are used to specifically tag unique samples in a sequencing run. Sequence should be reported in uppercase letters</td>
</tr>
<tr>
<td>mineral nutrient regimen (<a href="../0000570/">mineral_nutr_regm</a>)</td>
<td>Information about treatment involving the use of mineral supplements; should include the name of mineral nutrient, amount administered, treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include multiple mineral nutrient regimens</td>
</tr>
<tr>
<td>miscellaneous parameter (<a href="../0000752/">misc_param</a>)</td>
<td>Any other measurement performed or parameter collected, that is not listed here</td>
</tr>
<tr>
<td>mode of transmission (<a href="../0001312/">mode_transmission</a>)</td>
<td>The process through which the symbiotic host organism entered the host from which it was sampled</td>
</tr>
<tr>
<td>n-alkanes (<a href="../0000503/">n_alkanes</a>)</td>
<td>Concentration of n-alkanes; can include multiple n-alkanes</td>
</tr>
<tr>
<td>negative control type (<a href="../0001321/">neg_cont_type</a>)</td>
<td>The substance or equipment used as a negative control in an investigation</td>
</tr>
<tr>
<td>nitrate (<a href="../0000425/">nitrate</a>)</td>
<td>Concentration of nitrate in the sample</td>
</tr>
<tr>
<td>nitrite (<a href="../0000426/">nitrite</a>)</td>
<td>Concentration of nitrite in the sample</td>
</tr>
<tr>
<td>nitrogen (<a href="../0000504/">nitro</a>)</td>
<td>Concentration of nitrogen (total)</td>
</tr>
<tr>
<td>non-mineral nutrient regimen (<a href="../0000571/">non_min_nutr_regm</a>)</td>
<td>Information about treatment involving the exposure of plant to non-mineral nutrient such as oxygen, hydrogen or carbon; should include the name of non-mineral nutrient, amount administered, treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include multiple non-mineral nutrient regimens</td>
</tr>
<tr>
<td>nose/mouth/teeth/throat disorder (<a href="../0000283/">nose_mouth_teeth_throat_disord</a>)</td>
<td>History of nose/mouth/teeth/throat disorders; can include multiple disorders. The terms should be chosen from the DO (Human Disease Ontology) at <a href="http://www.disease-ontology.org">http://www.disease-ontology.org</a>, nose disease (<a href="https://disease-ontology.org/?id=DOID:2825">https://disease-ontology.org/?id=DOID:2825</a>), mouth disease (<a href="https://disease-ontology.org/?id=DOID:403">https://disease-ontology.org/?id=DOID:403</a>), tooth disease (<a href="https://disease-ontology.org/?id=DOID:1091">https://disease-ontology.org/?id=DOID:1091</a>), or upper respiratory tract disease (<a href="https://disease-ontology.org/?id=DOID:974">https://disease-ontology.org/?id=DOID:974</a>)</td>
</tr>
<tr>
<td>nose throat disorder (<a href="../0000270/">nose_throat_disord</a>)</td>
<td>History of nose-throat disorders; can include multiple disorders,  The terms should be chosen from the DO (Human Disease Ontology) at <a href="http://www.disease-ontology.org">http://www.disease-ontology.org</a>, lung disease (<a href="https://disease-ontology.org/?id=DOID:850">https://disease-ontology.org/?id=DOID:850</a>), upper respiratory tract disease (<a href="https://disease-ontology.org/?id=DOID:974">https://disease-ontology.org/?id=DOID:974</a>)</td>
</tr>
<tr>
<td>nucleic acid amplification (<a href="../0000038/">nucl_acid_amp</a>)</td>
<td>A link to a literature reference, electronic resource or a standard operating procedure (SOP), that describes the enzymatic amplification (PCR, TMA, NASBA) of specific nucleic acids</td>
</tr>
<tr>
<td>nucleic acid extraction (<a href="../0000037/">nucl_acid_ext</a>)</td>
<td>A link to a literature reference, electronic resource or a standard operating procedure (SOP), that describes the material separation to recover the nucleic acid fraction from a sample</td>
</tr>
<tr>
<td>nucleic acid extraction kit (<a href="../0001223/">nucl_acid_ext_kit</a>)</td>
<td>The name of the extraction kit used to recover the nucleic acid fraction of an input material is performed</td>
</tr>
<tr>
<td>number of replicons (<a href="../0000022/">num_replicons</a>)</td>
<td>Reports the number of replicons in a nuclear genome of eukaryotes, in the genome of a bacterium or archaea or the number of segments in a segmented virus. Always applied to the haploid chromosome count of a eukaryote</td>
</tr>
<tr>
<td>number of samples collected (<a href="../0001224/">num_samp_collect</a>)</td>
<td>The number of samples collected during the current sampling event</td>
</tr>
<tr>
<td>number of contigs (<a href="../0000060/">number_contig</a>)</td>
<td>Total number of contigs in the cleaned/submitted assembly that makes up a given genome, SAG, MAG, or UViG</td>
</tr>
<tr>
<td>number of pets (<a href="../0000231/">number_pets</a>)</td>
<td>The number of pets residing in the sampled space</td>
</tr>
<tr>
<td>number of houseplants (<a href="../0000230/">number_plants</a>)</td>
<td>The number of plant(s) in the sampling space</td>
</tr>
<tr>
<td>number of residents (<a href="../0000232/">number_resident</a>)</td>
<td>The number of individuals currently occupying in the sampling location</td>
</tr>
<tr>
<td>occupant density at sampling (<a href="../0000217/">occup_density_samp</a>)</td>
<td>Average number of occupants at time of sampling per square footage</td>
</tr>
<tr>
<td>occupancy documentation (<a href="../0000816/">occup_document</a>)</td>
<td>The type of documentation of occupancy</td>
</tr>
<tr>
<td>occupancy at sampling (<a href="../0000772/">occup_samp</a>)</td>
<td>Number of occupants present at time of sample within the given space</td>
</tr>
<tr>
<td>organic carbon (<a href="../0000508/">org_carb</a>)</td>
<td>Concentration of organic carbon</td>
</tr>
<tr>
<td>organism count qPCR information (<a href="../0000099/">org_count_qpcr_info</a>)</td>
<td>If qpcr was used for the cell count, the target gene name, the primer sequence and the cycling conditions should also be provided. (Example: 16S rrna; FWD:ACGTAGCTATGACGT REV:GTGCTAGTCGAGTAC; initial denaturation:90C_5min; denaturation:90C_2min; annealing:52C_30 sec; elongation:72C_30 sec; 90 C for 1 min; final elongation:72C_5min; 30 cycles)</td>
</tr>
<tr>
<td>organic matter (<a href="../0000204/">org_matter</a>)</td>
<td>Concentration of organic matter</td>
</tr>
<tr>
<td>organic nitrogen (<a href="../0000205/">org_nitro</a>)</td>
<td>Concentration of organic nitrogen</td>
</tr>
<tr>
<td>organic particles (<a href="../0000665/">org_particles</a>)</td>
<td>Concentration of particles such as faeces, hairs, food, vomit, paper fibers, plant material, humus, etc</td>
</tr>
<tr>
<td>organism count (<a href="../0000103/">organism_count</a>)</td>
<td>Total cell count of any organism (or group of organisms) per gram, volume or area of sample, should include name of organism followed by count. The method that was used for the enumeration (e.g. qPCR, atp, mpn, etc.) Should also be provided. (example: total prokaryotes; 3.5e7 cells per ml; qpcr)</td>
</tr>
<tr>
<td>OTU classification approach (<a href="../0000085/">otu_class_appr</a>)</td>
<td>Cutoffs and approach used when clustering  species-level  OTUs. Note that results from standard 95% ANI / 85% AF clustering should be provided alongside OTUS defined from another set of thresholds, even if the latter are the ones primarily used during the analysis</td>
</tr>
<tr>
<td>OTU database (<a href="../0000087/">otu_db</a>)</td>
<td>Reference database (i.e. sequences not generated as part of the current study) used to cluster new genomes in "species-level" OTUs, if any</td>
</tr>
<tr>
<td>OTU sequence comparison approach (<a href="../0000086/">otu_seq_comp_appr</a>)</td>
<td>Tool and thresholds used to compare sequences when computing "species-level" OTUs</td>
</tr>
<tr>
<td>oil water contact depth (<a href="../0000405/">owc_tvdss</a>)</td>
<td>Depth of the original oil water contact (OWC) zone (average) (m TVDSS)</td>
</tr>
<tr>
<td>oxygenation status of sample (<a href="../0000753/">oxy_stat_samp</a>)</td>
<td>Oxygenation status of sample</td>
</tr>
<tr>
<td>oxygen (<a href="../0000104/">oxygen</a>)</td>
<td>Oxygen (gas) amount or concentration at the time of sampling</td>
</tr>
<tr>
<td>particulate organic carbon (<a href="../0000515/">part_org_carb</a>)</td>
<td>Concentration of particulate organic carbon</td>
</tr>
<tr>
<td>particulate organic nitrogen (<a href="../0000719/">part_org_nitro</a>)</td>
<td>Concentration of particulate organic nitrogen</td>
</tr>
<tr>
<td>part of plant or animal (<a href="../0001149/">part_plant_animal</a>)</td>
<td>The anatomical part of the organism being involved in food production or consumption; e.g., a carrot is the root of the plant (root vegetable). This field accepts terms listed under part of plant or animal (<a href="http://purl.obolibrary.org/obo/FOODON_03420116">http://purl.obolibrary.org/obo/FOODON_03420116</a>)</td>
</tr>
<tr>
<td>particle classification (<a href="../0000206/">particle_class</a>)</td>
<td>Particles are classified, based on their size, into six general categories:clay, silt, sand, gravel, cobbles, and boulders; should include amount of particle preceded by the name of the particle type; can include multiple values</td>
</tr>
<tr>
<td>known pathogenicity (<a href="../0000027/">pathogenicity</a>)</td>
<td>To what is the entity pathogenic</td>
</tr>
<tr>
<td>pcr conditions (<a href="../0000049/">pcr_cond</a>)</td>
<td>Description of reaction conditions and components of PCR in the form of 'initial denaturation:94degC_1.5min; annealing=...'</td>
</tr>
<tr>
<td>pcr primers (<a href="../0000046/">pcr_primers</a>)</td>
<td>PCR primers that were used to amplify the sequence of the targeted gene, locus or subfragment. This field should contain all the primers used for a single PCR reaction if multiple forward or reverse primers are present in a single PCR reaction. The primer sequence should be reported in uppercase letters</td>
</tr>
<tr>
<td>permeability (<a href="../0000404/">permeability</a>)</td>
<td>Measure of the ability of a hydrocarbon resource to allow fluids to pass through it. (Additional information: <a href="https://en.wikipedia.org/wiki/Permeability_(earth_sciences">https://en.wikipedia.org/wiki/Permeability_(earth_sciences</a>))</td>
</tr>
<tr>
<td>perturbation (<a href="../0000754/">perturbation</a>)</td>
<td>Type of perturbation, e.g. chemical administration, physical disturbance, etc., coupled with perturbation regimen including how many times the perturbation was repeated, how long each perturbation lasted, and the start and end time of the entire perturbation period; can include multiple perturbation types</td>
</tr>
<tr>
<td>pesticide regimen (<a href="../0000573/">pesticide_regm</a>)</td>
<td>Information about treatment involving use of insecticides; should include the name of pesticide, amount administered, treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include multiple pesticide regimens</td>
</tr>
<tr>
<td>presence of pets or farm animals (<a href="../0000267/">pet_farm_animal</a>)</td>
<td>Specification of presence of pets or farm animals in the environment of subject, if yes the animals should be specified; can include multiple animals present</td>
</tr>
<tr>
<td>petroleum hydrocarbon (<a href="../0000516/">petroleum_hydrocarb</a>)</td>
<td>Concentration of petroleum hydrocarbon</td>
</tr>
<tr>
<td>pH (<a href="../0001001/">ph</a>)</td>
<td>Ph measurement of the sample, or liquid portion of sample, or aqueous phase of the fluid</td>
</tr>
<tr>
<td>pH method (<a href="../0001106/">ph_meth</a>)</td>
<td>Reference or method used in determining pH</td>
</tr>
<tr>
<td>pH regimen (<a href="../0001056/">ph_regm</a>)</td>
<td>Information about treatment involving exposure of plants to varying levels of ph of the growth media, treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include multiple regimen</td>
</tr>
<tr>
<td>phaeopigments (<a href="../0000180/">phaeopigments</a>)</td>
<td>Concentration of phaeopigments; can include multiple phaeopigments</td>
</tr>
<tr>
<td>phosphate (<a href="../0000505/">phosphate</a>)</td>
<td>Concentration of phosphate</td>
</tr>
<tr>
<td>phospholipid fatty acid (<a href="../0000181/">phosplipid_fatt_acid</a>)</td>
<td>Concentration of phospholipid fatty acids; can include multiple values</td>
</tr>
<tr>
<td>photon flux (<a href="../0000725/">photon_flux</a>)</td>
<td>Measurement of photon flux</td>
</tr>
<tr>
<td>photosynthetic activity (<a href="../0001296/">photosynt_activ</a>)</td>
<td>Measurement of photosythetic activity (i.e. leaf gas exchange / chlorophyll fluorescence emissions / reflectance / transpiration) Please also include the term method term detailing the method of activity measurement</td>
</tr>
<tr>
<td>photosynthetic activity method (<a href="../0001336/">photosynt_activ_meth</a>)</td>
<td>Reference or method used in measurement of photosythetic activity</td>
</tr>
<tr>
<td>plant growth medium (<a href="../0001057/">plant_growth_med</a>)</td>
<td>Specification of the media for growing the plants or tissue cultured samples, e.g. soil, aeroponic, hydroponic, in vitro solid culture medium, in vitro liquid culture medium. Recommended value is a specific value from EO:plant growth medium (follow this link for terms <a href="http://purl.obolibrary.org/obo/EO_0007147">http://purl.obolibrary.org/obo/EO_0007147</a>) or other controlled vocabulary</td>
</tr>
<tr>
<td>degree of plant part maturity (<a href="../0001120/">plant_part_maturity</a>)</td>
<td>A description of the stage of development of a plant or plant part based on maturity or ripeness. This field accepts terms listed under degree of plant maturity (<a href="http://purl.obolibrary.org/obo/FOODON_03530050">http://purl.obolibrary.org/obo/FOODON_03530050</a>)</td>
</tr>
<tr>
<td>plant product (<a href="../0001058/">plant_product</a>)</td>
<td>Substance produced by the plant, where the sample was obtained from</td>
</tr>
<tr>
<td>plant reproductive part (<a href="../0001150/">plant_reprod_crop</a>)</td>
<td>Plant reproductive part used in the field during planting to start the crop</td>
</tr>
<tr>
<td>plant sex (<a href="../0001059/">plant_sex</a>)</td>
<td>Sex of the reproductive parts on the whole plant, e.g. pistillate, staminate, monoecieous, hermaphrodite</td>
</tr>
<tr>
<td>plant structure (<a href="../0001060/">plant_struc</a>)</td>
<td>Name of plant structure the sample was obtained from; for Plant Ontology (PO) (v releases/2017-12-14) terms, see <a href="http://purl.bioontology.org/ontology/PO">http://purl.bioontology.org/ontology/PO</a>, e.g. petiole epidermis (PO_0000051). If an individual flower is sampled, the sex of it can be recorded here</td>
</tr>
<tr>
<td>plant water delivery method (<a href="../0001111/">plant_water_method</a>)</td>
<td>Description of the equipment or method used to distribute water to crops. This field accepts termed listed under irrigation process (<a href="http://purl.obolibrary.org/obo/AGRO_00000006">http://purl.obolibrary.org/obo/AGRO_00000006</a>). Multiple terms can be separated by pipes</td>
</tr>
<tr>
<td>ploidy (<a href="../0000021/">ploidy</a>)</td>
<td>The ploidy level of the genome (e.g. allopolyploid, haploid, diploid, triploid, tetraploid). It has implications for the downstream study of duplicated gene and regions of the genomes (and perhaps for difficulties in assembly). For terms, please select terms listed under class ploidy (PATO:001374) of Phenotypic Quality Ontology (PATO), and for a browser of PATO (v 2018-03-27) please refer to <a href="http://purl.bioontology.org/ontology/PATO">http://purl.bioontology.org/ontology/PATO</a></td>
</tr>
<tr>
<td>pollutants (<a href="../0000107/">pollutants</a>)</td>
<td>Pollutant types and, amount or concentrations measured at the time of sampling; can report multiple pollutants by entering numeric values preceded by name of pollutant</td>
</tr>
<tr>
<td>pooling of DNA extracts (if done) (<a href="../0000325/">pool_dna_extracts</a>)</td>
<td>Indicate whether multiple DNA extractions were mixed. If the answer yes, the number of extracts that were pooled should be given</td>
</tr>
<tr>
<td>porosity (<a href="../0000211/">porosity</a>)</td>
<td>Porosity of deposited sediment is volume of voids divided by the total volume of sample</td>
</tr>
<tr>
<td>positive control type (<a href="../0001322/">pos_cont_type</a>)</td>
<td>The substance, mixture, product, or apparatus used to verify that a process which is part of an investigation delivers a true positive</td>
</tr>
<tr>
<td>potassium (<a href="../0000430/">potassium</a>)</td>
<td>Concentration of potassium in the sample</td>
</tr>
<tr>
<td>pour point (<a href="../0000127/">pour_point</a>)</td>
<td>Temperature at which a liquid becomes semi solid and loses its flow characteristics. In crude oil a high  pour point  is generally associated with a high paraffin content, typically found in crude deriving from a larger proportion of plant material. (soure: <a href="https://en.wikipedia.org/wiki/pour_point">https://en.wikipedia.org/wiki/pour_point</a>)</td>
</tr>
<tr>
<td>pre-treatment (<a href="../0000348/">pre_treatment</a>)</td>
<td>The process of pre-treatment removes materials that can be easily collected from the raw wastewater</td>
</tr>
<tr>
<td>predicted genome structure (<a href="../0000083/">pred_genome_struc</a>)</td>
<td>Expected structure of the viral genome</td>
</tr>
<tr>
<td>predicted genome type (<a href="../0000082/">pred_genome_type</a>)</td>
<td>Type of genome predicted for the UViG</td>
</tr>
<tr>
<td>pregnancy (<a href="../0000966/">pregnancy</a>)</td>
<td>Date due of pregnancy</td>
</tr>
<tr>
<td>presence of pets, animals, or insects (<a href="../0000819/">pres_animal_insect</a>)</td>
<td>The type and number of animals or insects present in the sampling space</td>
</tr>
<tr>
<td>pressure (<a href="../0000412/">pressure</a>)</td>
<td>Pressure to which the sample is subject to, in atmospheres</td>
</tr>
<tr>
<td>history/previous land use method (<a href="../0000316/">prev_land_use_meth</a>)</td>
<td>Reference or method used in determining previous land use and dates</td>
</tr>
<tr>
<td>history/previous land use (<a href="../0000315/">previous_land_use</a>)</td>
<td>Previous land use and dates</td>
</tr>
<tr>
<td>primary production (<a href="../0000728/">primary_prod</a>)</td>
<td>Measurement of primary production, generally measured as isotope uptake</td>
</tr>
<tr>
<td>primary treatment (<a href="../0000349/">primary_treatment</a>)</td>
<td>The process to produce both a generally homogeneous liquid capable of being treated biologically and a sludge that can be separately treated or processed</td>
</tr>
<tr>
<td>production labeling claims (<a href="../prod_label_claims/">prod_label_claims</a>)</td>
<td>Labeling claims containing descriptors such as wild caught, free-range, organic, free-range, industrial, hormone-free, antibiotic free, cage free. Can include more than one term, separated by ";"</td>
</tr>
<tr>
<td>production rate (<a href="../0000452/">prod_rate</a>)</td>
<td>Oil and/or gas production rates per well (e.g. 524 m3 / day)</td>
</tr>
<tr>
<td>production start date (<a href="../0001008/">prod_start_date</a>)</td>
<td>Date of field's first production</td>
</tr>
<tr>
<td>profile position (<a href="../0001084/">profile_position</a>)</td>
<td>Cross-sectional position in the hillslope where sample was collected.sample area position in relation to surrounding areas</td>
</tr>
<tr>
<td>project name (<a href="../0000092/">project_name</a>)</td>
<td>Name of the project within which the sequencing was organized</td>
</tr>
<tr>
<td>propagation (<a href="../0000033/">propagation</a>)</td>
<td>The type of reproduction from the parent stock. Values for this field is specific to different taxa. For phage or virus: lytic/lysogenic/temperate/obligately lytic. For plasmids: incompatibility group. For eukaryotes: sexual/asexual</td>
</tr>
<tr>
<td>lung/pulmonary disorder (<a href="../0000269/">pulmonary_disord</a>)</td>
<td>History of pulmonary disorders; can include multiple disorders. The terms should be chosen from the DO (Human Disease Ontology) at <a href="http://www.disease-ontology.org">http://www.disease-ontology.org</a>, lung disease (<a href="https://disease-ontology.org/?id=DOID:850">https://disease-ontology.org/?id=DOID:850</a>)</td>
</tr>
<tr>
<td>quadrant position (<a href="../0000820/">quad_pos</a>)</td>
<td>The quadrant position of the sampling room within the building</td>
</tr>
<tr>
<td>radiation regimen (<a href="../0000575/">radiation_regm</a>)</td>
<td>Information about treatment involving exposure of plant or a plant part to a particular radiation regimen; should include the radiation type, amount or intensity administered, treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include multiple radiation regimens</td>
</tr>
<tr>
<td>rainfall regimen (<a href="../0000576/">rainfall_regm</a>)</td>
<td>Information about treatment involving an exposure to a given amount of rainfall, treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include multiple regimens</td>
</tr>
<tr>
<td>reactor type (<a href="../0000350/">reactor_type</a>)</td>
<td>Anaerobic digesters can be designed and engineered to operate using a number of different process configurations, as batch or continuous, mesophilic, high solid or low solid, and single stage or multistage</td>
</tr>
<tr>
<td>reassembly post binning (<a href="../0000079/">reassembly_bin</a>)</td>
<td>Has an assembly been performed on a genome bin extracted from a metagenomic assembly?</td>
</tr>
<tr>
<td>redox potential (<a href="../0000182/">redox_potential</a>)</td>
<td>Redox potential, measured relative to a hydrogen cell, indicating oxidation or reduction potential</td>
</tr>
<tr>
<td>reference for biomaterial (<a href="../0000025/">ref_biomaterial</a>)</td>
<td>Primary publication if isolated before genome publication; otherwise, primary genome report</td>
</tr>
<tr>
<td>reference database(s) (<a href="../0000062/">ref_db</a>)</td>
<td>List of database(s) used for ORF annotation, along with version number and reference to website or publication</td>
</tr>
<tr>
<td>relative air humidity (<a href="../0000121/">rel_air_humidity</a>)</td>
<td>Partial vapor and air pressure, density of the vapor and air, or by the actual mass of the vapor and air</td>
</tr>
<tr>
<td>outside relative humidity (<a href="../0000188/">rel_humidity_out</a>)</td>
<td>The recorded outside relative humidity value at the time of sampling</td>
</tr>
<tr>
<td>relative location of sample (<a href="../0001161/">rel_location</a>)</td>
<td>Location of sampled soil to other parts of the farm e.g. under crop plant, near irrigation ditch, from the dirt road</td>
</tr>
<tr>
<td>relative sampling location (<a href="../0000821/">rel_samp_loc</a>)</td>
<td>The sampling location within the train car</td>
</tr>
<tr>
<td>relationship to oxygen (<a href="../0000015/">rel_to_oxygen</a>)</td>
<td>Is this organism an aerobe, anaerobe? Please note that aerobic and anaerobic are valid descriptors for microbial environments</td>
</tr>
<tr>
<td>repository name (<a href="../0001152/">repository_name</a>)</td>
<td>The name of the institution where the sample or DNA extract is held or "sample not available" if the sample was used in its entirety for analysis or otherwise not retained</td>
</tr>
<tr>
<td>reservoir name (<a href="../0000303/">reservoir</a>)</td>
<td>Name of the reservoir (e.g. Carapebus)</td>
</tr>
<tr>
<td>resins wt% (<a href="../0000134/">resins_pc</a>)</td>
<td>Saturate, Aromatic, Resin and Asphaltene  (SARA) is an analysis method that divides  crude oil  components according to their polarizability and polarity. There are three main methods to obtain SARA results. The most popular one is known as the Iatroscan TLC-FID and is referred to as IP-143 (source: <a href="https://en.wikipedia.org/wiki/Saturate,_aromatic,_resin_and_asphaltene">https://en.wikipedia.org/wiki/Saturate,_aromatic,_resin_and_asphaltene</a>)</td>
</tr>
<tr>
<td>room air exchange rate (<a href="../0000169/">room_air_exch_rate</a>)</td>
<td>The rate at which outside air replaces indoor air in a given space</td>
</tr>
<tr>
<td>room architectural elements (<a href="../0000233/">room_architec_elem</a>)</td>
<td>The unique details and component parts that, together, form the architecture of a distinguisahable space within a built structure</td>
</tr>
<tr>
<td>room condition (<a href="../0000822/">room_condt</a>)</td>
<td>The condition of the room at the time of sampling</td>
</tr>
<tr>
<td>rooms connected by a doorway (<a href="../0000826/">room_connected</a>)</td>
<td>List of rooms connected to the sampling room by a doorway</td>
</tr>
<tr>
<td>room count (<a href="../0000234/">room_count</a>)</td>
<td>The total count of rooms in the built structure including all room types</td>
</tr>
<tr>
<td>room dimensions (<a href="../0000192/">room_dim</a>)</td>
<td>The length, width and height of sampling room</td>
</tr>
<tr>
<td>room door distance (<a href="../0000193/">room_door_dist</a>)</td>
<td>Distance between doors (meters) in the hallway between the sampling room and adjacent rooms</td>
</tr>
<tr>
<td>rooms that share a door with sampling room (<a href="../0000242/">room_door_share</a>)</td>
<td>List of room(s) (room number, room name) sharing a door with the sampling room</td>
</tr>
<tr>
<td>rooms that are on the same hallway (<a href="../0000238/">room_hallway</a>)</td>
<td>List of room(s) (room number, room name) located in the same hallway as sampling room</td>
</tr>
<tr>
<td>room location in building (<a href="../0000823/">room_loc</a>)</td>
<td>The position of the room within the building</td>
</tr>
<tr>
<td>room moisture damage or mold history (<a href="../0000235/">room_moist_dam_hist</a>)</td>
<td>The history of moisture damage or mold in the past 12 months. Number of events of moisture damage or mold observed</td>
</tr>
<tr>
<td>room net area (<a href="../0000194/">room_net_area</a>)</td>
<td>The net floor area of sampling room. Net area excludes wall thicknesses</td>
</tr>
<tr>
<td>room occupancy (<a href="../0000236/">room_occup</a>)</td>
<td>Count of room occupancy at time of sampling</td>
</tr>
<tr>
<td>room sampling position (<a href="../0000824/">room_samp_pos</a>)</td>
<td>The horizontal sampling position in the room relative to architectural elements</td>
</tr>
<tr>
<td>room type (<a href="../0000825/">room_type</a>)</td>
<td>The main purpose or activity of the sampling room. A room is any distinguishable space within a structure</td>
</tr>
<tr>
<td>room volume (<a href="../0000195/">room_vol</a>)</td>
<td>Volume of sampling room</td>
</tr>
<tr>
<td>rooms that share a wall with sampling room (<a href="../0000243/">room_wall_share</a>)</td>
<td>List of room(s) (room number, room name) sharing a wall with the sampling room</td>
</tr>
<tr>
<td>room window count (<a href="../0000237/">room_window_count</a>)</td>
<td>Number of windows in the room</td>
</tr>
<tr>
<td>rooting conditions (<a href="../0001061/">root_cond</a>)</td>
<td>Relevant rooting conditions such as field plot size, sowing density, container dimensions, number of plants per container</td>
</tr>
<tr>
<td>rooting medium carbon (<a href="../0000577/">root_med_carbon</a>)</td>
<td>Source of organic carbon in the culture rooting medium; e.g. sucrose</td>
</tr>
<tr>
<td>rooting medium macronutrients (<a href="../0000578/">root_med_macronutr</a>)</td>
<td>Measurement of the culture rooting medium macronutrients (N,P, K, Ca, Mg, S); e.g. KH2PO4 (170 mg/L)</td>
</tr>
<tr>
<td>rooting medium micronutrients (<a href="../0000579/">root_med_micronutr</a>)</td>
<td>Measurement of the culture rooting medium micronutrients (Fe, Mn, Zn, B, Cu, Mo); e.g. H3BO3 (6.2 mg/L)</td>
</tr>
<tr>
<td>rooting medium pH (<a href="../0001062/">root_med_ph</a>)</td>
<td>pH measurement of the culture rooting medium; e.g. 5.5</td>
</tr>
<tr>
<td>rooting medium regulators (<a href="../0000581/">root_med_regl</a>)</td>
<td>Growth regulators in the culture rooting medium such as cytokinins, auxins, gybberellins, abscisic acid; e.g. 0.5  mg/L NAA</td>
</tr>
<tr>
<td>rooting medium solidifier (<a href="../0001063/">root_med_solid</a>)</td>
<td>Specification of the solidifying agent in the culture rooting medium; e.g. agar</td>
</tr>
<tr>
<td>rooting medium organic supplements (<a href="../0000580/">root_med_suppl</a>)</td>
<td>Organic supplements of the culture rooting medium, such as vitamins, amino acids, organic acids, antibiotics activated charcoal; e.g. nicotinic acid (0.5  mg/L)</td>
</tr>
<tr>
<td>route of transmission (<a href="../0001316/">route_transmission</a>)</td>
<td>Description of path taken by the symbiotic host organism being sampled in order to establish a symbiotic relationship with the host (with which it was observed at the time of sampling) via a mode of transmission (specified in mode_transmission)</td>
</tr>
<tr>
<td>salinity (<a href="../0000183/">salinity</a>)</td>
<td>The total concentration of all dissolved salts in a liquid or solid sample. While salinity can be measured by a complete chemical analysis, this method is difficult and time consuming. More often, it is instead derived from the conductivity measurement. This is known as practical salinity. These derivations compare the specific conductance of the sample to a salinity standard such as seawater</td>
</tr>
<tr>
<td>salt regimen (<a href="../0000582/">salt_regm</a>)</td>
<td>Information about treatment involving use of salts as supplement to liquid and soil growth media; should include the name of salt, amount administered, treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include multiple salt regimens</td>
</tr>
<tr>
<td>sample capture status (<a href="../0000860/">samp_capt_status</a>)</td>
<td>Reason for the sample</td>
</tr>
<tr>
<td>sample collection device (<a href="../0000002/">samp_collect_device</a>)</td>
<td>The device used to collect an environmental sample. This field accepts terms listed under environmental sampling device (<a href="http://purl.obolibrary.org/obo/ENVO">http://purl.obolibrary.org/obo/ENVO</a>). This field also accepts terms listed under specimen collection device (<a href="http://purl.obolibrary.org/obo/GENEPIO_0002094">http://purl.obolibrary.org/obo/GENEPIO_0002094</a>)</td>
</tr>
<tr>
<td>sample collection method (<a href="../0001225/">samp_collect_method</a>)</td>
<td>The method employed for collecting the sample</td>
</tr>
<tr>
<td>sample collection point (<a href="../0001015/">samp_collect_point</a>)</td>
<td>Sampling point on the asset were sample was collected (e.g. Wellhead, storage tank, separator, etc). If "other" is specified, please propose entry in "additional info" field</td>
</tr>
<tr>
<td>sample disease stage (<a href="../0000249/">samp_dis_stage</a>)</td>
<td>Stage of the disease at the time of sample collection, e.g. inoculation, penetration, infection, growth and reproduction, dissemination of pathogen</td>
</tr>
<tr>
<td>sampling floor (<a href="../0000828/">samp_floor</a>)</td>
<td>The floor of the building, where the sampling room is located</td>
</tr>
<tr>
<td>sample location condition (<a href="../0001257/">samp_loc_condition</a>)</td>
<td>The condition of the sample location at the time of sampling</td>
</tr>
<tr>
<td>corrosion rate at sample location (<a href="../0000136/">samp_loc_corr_rate</a>)</td>
<td>Metal corrosion rate is the speed of metal deterioration due to environmental conditions. As environmental conditions change corrosion rates change accordingly. Therefore, long term corrosion rates are generally more informative than short term rates and for that reason they are preferred during reporting. In the case of suspected MIC, corrosion rate measurements at the time of sampling might provide insights into the involvement of certain microbial community members in MIC as well as potential microbial interplays</td>
</tr>
<tr>
<td>sample material processing (<a href="../0000016/">samp_mat_process</a>)</td>
<td>A brief description of any processing applied to the sample during or after retrieving the sample from environment, or a link to the relevant protocol(s) performed</td>
</tr>
<tr>
<td>sample measured depth (<a href="../0000413/">samp_md</a>)</td>
<td>In non deviated well, measured depth is equal to the true vertical depth, TVD (TVD=TVDSS plus the reference or datum it refers to). In deviated wells, the MD is the length of trajectory of the borehole measured from the same reference or datum. Common datums used are ground level (GL), drilling rig floor (DF), rotary table (RT), kelly bushing (KB) and mean sea level (MSL). If "other" is specified, please propose entry in "additional info" field</td>
</tr>
<tr>
<td>sample name (<a href="../0001107/">samp_name</a>)</td>
<td>A local identifier or name that for the material sample used for extracting nucleic acids, and subsequent sequencing. It can refer either to the original material collected or to any derived sub-samples. It can have any format, but we suggest that you make it concise, unique and consistent within your lab, and as informative as possible. INSDC requires every sample name from a single Submitter to be unique. Use of a globally unique identifier for the field source_mat_id is recommended in addition to sample_name</td>
</tr>
<tr>
<td>sample pooling (<a href="../0001153/">samp_pooling</a>)</td>
<td>Physical combination of several instances of like material, e.g. RNA extracted from samples or dishes of cell cultures into one big aliquot of cells. Please provide a short description of the samples that were pooled</td>
</tr>
<tr>
<td>preservative added to sample (<a href="../0000463/">samp_preserv</a>)</td>
<td>Preservative added to the sample (e.g. Rnalater, alcohol, formaldehyde, etc.). Where appropriate include volume added (e.g. Rnalater; 2 ml)</td>
</tr>
<tr>
<td>purpose of sampling (<a href="../0001151/">samp_purpose</a>)</td>
<td>The reason that the sample was collected</td>
</tr>
<tr>
<td>biological sample replicate (<a href="../0001226/">samp_rep_biol</a>)</td>
<td>Measurements of biologically distinct samples that show biological variation</td>
</tr>
<tr>
<td>technical sample replicate (<a href="../0001227/">samp_rep_tech</a>)</td>
<td>Repeated measurements of the same sample that show independent measures of the noise associated with the equipment and the protocols</td>
</tr>
<tr>
<td>sampling room ID or name (<a href="../0000244/">samp_room_id</a>)</td>
<td>Sampling room number. This ID should be consistent with the designations on the building floor plans</td>
</tr>
<tr>
<td>amount or size of sample collected (<a href="../0000001/">samp_size</a>)</td>
<td>The total amount or size (volume (ml), mass (g) or area (m2) ) of sample collected</td>
</tr>
<tr>
<td>sample size sorting method (<a href="../0000216/">samp_sort_meth</a>)</td>
<td>Method by which samples are sorted; open face filter collecting total suspended particles, prefilter to remove particles larger than X micrometers in diameter, where common values of X would be 10 and 2.5 full size sorting in a cascade impactor</td>
</tr>
<tr>
<td>sample source material category (<a href="../0001154/">samp_source_mat_cat</a>)</td>
<td>This is the scientific role or category that the subject organism or material has with respect to an investigation.  This field accepts terms listed under specimen source material category (<a href="http://purl.obolibrary.org/obo/GENEPIO_0001237">http://purl.obolibrary.org/obo/GENEPIO_0001237</a> or <a href="http://purl.obolibrary.org/obo/OBI_0100051">http://purl.obolibrary.org/obo/OBI_0100051</a>)</td>
</tr>
<tr>
<td>sample storage device (<a href="../0001228/">samp_stor_device</a>)</td>
<td>The container used to store the  sample. This field accepts terms listed under container (<a href="http://purl.obolibrary.org/obo/NCIT_C43186">http://purl.obolibrary.org/obo/NCIT_C43186</a>). If the proper descriptor is not listed please use text to describe the storage device</td>
</tr>
<tr>
<td>sample storage media (<a href="../0001229/">samp_stor_media</a>)</td>
<td>The liquid that is added to the sample collection device prior to sampling. If the sample is pre-hydrated, indicate the liquid media the sample is pre-hydrated with for storage purposes. This field accepts terms listed under microbiological culture medium (<a href="http://purl.obolibrary.org/obo/MICRO_0000067">http://purl.obolibrary.org/obo/MICRO_0000067</a>). If the proper descriptor is not listed please use text to describe the sample storage media</td>
</tr>
<tr>
<td>sample storage duration (<a href="../0000116/">samp_store_dur</a>)</td>
<td>Duration for which the sample was stored. Indicate the duration for which the sample was stored written in ISO 8601 format</td>
</tr>
<tr>
<td>sample storage location (<a href="../0000755/">samp_store_loc</a>)</td>
<td>Location at which sample was stored, usually name of a specific freezer/room</td>
</tr>
<tr>
<td>sample storage solution (<a href="../0001317/">samp_store_sol</a>)</td>
<td>Solution within which sample was stored, if any</td>
</tr>
<tr>
<td>sample storage temperature (<a href="../0000110/">samp_store_temp</a>)</td>
<td>Temperature at which sample was stored, e.g. -80 degree Celsius</td>
</tr>
<tr>
<td>sample subtype (<a href="../0000999/">samp_subtype</a>)</td>
<td>Name of sample sub-type. For example if "sample type" is "Produced Water" then subtype could be "Oil Phase" or "Water Phase". If "other" is specified, please propose entry in "additional info" field</td>
</tr>
<tr>
<td>sample surface moisture (<a href="../0001256/">samp_surf_moisture</a>)</td>
<td>Degree of water held on a sampled surface.  If present, user can state the degree of water held on surface (intermittent moisture, submerged). If no surface moisture is present indicate not present</td>
</tr>
<tr>
<td>taxonomy ID of DNA sample (<a href="../0001320/">samp_taxon_id</a>)</td>
<td>NCBI taxon id of the sample.  Maybe be a single taxon or mixed taxa sample. Use 'synthetic metagenome  for mock community/positive controls, or 'blank sample' for negative controls</td>
</tr>
<tr>
<td>sampling time outside (<a href="../0000196/">samp_time_out</a>)</td>
<td>The recent and long term history of outside sampling</td>
</tr>
<tr>
<td>sample transport conditions (<a href="../0000410/">samp_transport_cond</a>)</td>
<td>Sample transport duration (in days or hrs) and temperature the sample was exposed to (e.g. 5.5 days; 20   C)</td>
</tr>
<tr>
<td>sample transport  container (<a href="../0001230/">samp_transport_cont</a>)</td>
<td>Conatiner in which the sample was stored during transport. Indicate the location name</td>
</tr>
<tr>
<td>sample transport duration (<a href="../0001231/">samp_transport_dur</a>)</td>
<td>The duration of time from when the sample was collected until processed. Indicate the duration for which the sample was stored written in ISO 8601 format</td>
</tr>
<tr>
<td>sample transport temperature (<a href="../0001232/">samp_transport_temp</a>)</td>
<td>Temperature at which sample was transported, e.g. -20 or 4 degree Celsius</td>
</tr>
<tr>
<td>sample true vertical depth subsea (<a href="../0000409/">samp_tvdss</a>)</td>
<td>Depth of the sample i.e. The vertical distance between the sea level and the sampled position in the subsurface. Depth can be reported as an interval for subsurface samples e.g. 1325.75-1362.25 m</td>
</tr>
<tr>
<td>sample type (<a href="../0000998/">samp_type</a>)</td>
<td>The type of material from which the sample was obtained. For the Hydrocarbon package, samples include types like core, rock trimmings, drill cuttings, piping section, coupon, pigging debris, solid deposit, produced fluid, produced water, injected water, swabs, etc. For the Food Package, samples are usually categorized as food, body products or tissues, or environmental material. This field accepts terms listed under environmental specimen (<a href="http://purl.obolibrary.org/obo/GENEPIO_0001246">http://purl.obolibrary.org/obo/GENEPIO_0001246</a>)</td>
</tr>
<tr>
<td>sample volume or weight for DNA extraction (<a href="../0000111/">samp_vol_we_dna_ext</a>)</td>
<td>Volume (ml) or mass (g) of total collected sample processed for DNA extraction. Note: total sample collected should be entered under the term Sample Size (MIXS:0000001)</td>
</tr>
<tr>
<td>sampling day weather (<a href="../0000827/">samp_weather</a>)</td>
<td>The weather on the sampling day</td>
</tr>
<tr>
<td>sample well name (<a href="../0000296/">samp_well_name</a>)</td>
<td>Name of the well (e.g. BXA1123) where sample was taken</td>
</tr>
<tr>
<td>saturates wt% (<a href="../0000131/">saturates_pc</a>)</td>
<td>Saturate, Aromatic, Resin and Asphaltene  (SARA) is an analysis method that divides  crude oil  components according to their polarizability and polarity. There are three main methods to obtain SARA results. The most popular one is known as the Iatroscan TLC-FID and is referred to as IP-143 (source: <a href="https://en.wikipedia.org/wiki/Saturate,_aromatic,_resin_and_asphaltene">https://en.wikipedia.org/wiki/Saturate,_aromatic,_resin_and_asphaltene</a>)</td>
</tr>
<tr>
<td>single cell or viral particle lysis approach (<a href="../0000076/">sc_lysis_approach</a>)</td>
<td>Method used to free DNA from interior of the cell(s) or particle(s)</td>
</tr>
<tr>
<td>single cell or viral particle lysis kit protocol (<a href="../0000054/">sc_lysis_method</a>)</td>
<td>Name of the kit or standard protocol used for cell(s) or particle(s) lysis</td>
</tr>
<tr>
<td>season (<a href="../0000829/">season</a>)</td>
<td>The season when sampling occurred. Any of the four periods into which the year is divided by the equinoxes and solstices. This field accepts terms listed under season (<a href="http://purl.obolibrary.org/obo/NCIT_C94729">http://purl.obolibrary.org/obo/NCIT_C94729</a>)</td>
</tr>
<tr>
<td>seasonal environment (<a href="../0001068/">season_environment</a>)</td>
<td>Treatment involving an exposure to a particular season (e.g. Winter, summer, rabi, rainy etc.), treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment</td>
</tr>
<tr>
<td>mean seasonal humidity (<a href="../0001148/">season_humidity</a>)</td>
<td>Average humidity of the region throughout the growing season</td>
</tr>
<tr>
<td>mean seasonal precipitation (<a href="../0000645/">season_precpt</a>)</td>
<td>The average of all seasonal precipitation values known, or an estimated equivalent value derived by such methods as regional indexes or Isohyetal maps</td>
</tr>
<tr>
<td>mean seasonal temperature (<a href="../0000643/">season_temp</a>)</td>
<td>Mean seasonal temperature</td>
</tr>
<tr>
<td>seasonal use (<a href="../0000830/">season_use</a>)</td>
<td>The seasons the space is occupied</td>
</tr>
<tr>
<td>secondary treatment (<a href="../0000351/">secondary_treatment</a>)</td>
<td>The process for substantially degrading the biological content of the sewage</td>
</tr>
<tr>
<td>sediment type (<a href="../0001078/">sediment_type</a>)</td>
<td>Information about the sediment type based on major constituents</td>
</tr>
<tr>
<td>sequencing method (<a href="../0000050/">seq_meth</a>)</td>
<td>Sequencing machine used. Where possible the term should be taken from the OBI list of DNA sequencers (<a href="http://purl.obolibrary.org/obo/OBI_0400103">http://purl.obolibrary.org/obo/OBI_0400103</a>)</td>
</tr>
<tr>
<td>sequence quality check (<a href="../0000051/">seq_quality_check</a>)</td>
<td>Indicate if the sequence has been called by automatic systems (none) or undergone a manual editing procedure (e.g. by inspecting the raw data or chromatograms). Applied only for sequences that are not submitted to SRA,ENA or DRA</td>
</tr>
<tr>
<td>sequencing kit (<a href="../0001155/">sequencing_kit</a>)</td>
<td>Pre-filled, ready-to-use reagent cartridges. Used to produce improved chemistry, cluster density and read length as well as improve quality (Q) scores. Reagent components are encoded to interact with the sequencing system to validate compatibility with user-defined applications. Indicate name of the sequencing kit</td>
</tr>
<tr>
<td>sequencing location (<a href="../0001156/">sequencing_location</a>)</td>
<td>The location the sequencing run was performed. Indicate the name of the lab or core facility where samples were sequenced</td>
</tr>
<tr>
<td>serovar or serotype (<a href="../0001157/">serovar_or_serotype</a>)</td>
<td>A characterization of a cell or microorganism based on the antigenic properties of the molecules on its surface. Indicate the name of a serovar or serotype of interest. This field accepts terms under organism (<a href="http://purl.obolibrary.org/obo/NCIT_C14250">http://purl.obolibrary.org/obo/NCIT_C14250</a>). This field also accepts identification numbers from NCBI under <a href="https://www.ncbi.nlm.nih.gov/taxonomy">https://www.ncbi.nlm.nih.gov/taxonomy</a></td>
</tr>
<tr>
<td>sewage type (<a href="../0000215/">sewage_type</a>)</td>
<td>Type of wastewater treatment plant as municipial or industrial</td>
</tr>
<tr>
<td>sexual activity (<a href="../0000285/">sexual_act</a>)</td>
<td>Current sexual partner and frequency of sex</td>
</tr>
<tr>
<td>shading device signs of water/mold (<a href="../0000834/">shad_dev_water_mold</a>)</td>
<td>Signs of the presence of mold or mildew on the shading device</td>
</tr>
<tr>
<td>shading device condition (<a href="../0000831/">shading_device_cond</a>)</td>
<td>The physical condition of the shading device at the time of sampling</td>
</tr>
<tr>
<td>shading device location (<a href="../0000832/">shading_device_loc</a>)</td>
<td>The location of the shading device in relation to the built structure</td>
</tr>
<tr>
<td>shading device material (<a href="../0000245/">shading_device_mat</a>)</td>
<td>The material the shading device is composed of</td>
</tr>
<tr>
<td>shading device type (<a href="../0000835/">shading_device_type</a>)</td>
<td>The type of shading device</td>
</tr>
<tr>
<td>sieving (<a href="../0000322/">sieving</a>)</td>
<td>Collection design of pooled samples and/or sieve size and amount of sample sieved</td>
</tr>
<tr>
<td>silicate (<a href="../0000184/">silicate</a>)</td>
<td>Concentration of silicate</td>
</tr>
<tr>
<td>similarity search method (<a href="../0000063/">sim_search_meth</a>)</td>
<td>Tool used to compare ORFs with database, along with version and cutoffs used</td>
</tr>
<tr>
<td>size fraction selected (<a href="../0000017/">size_frac</a>)</td>
<td>Filtering pore size used in sample preparation</td>
</tr>
<tr>
<td>size-fraction lower threshold (<a href="../0000735/">size_frac_low</a>)</td>
<td>Refers to the mesh/pore size used to pre-filter/pre-sort the sample. Materials larger than the size threshold are excluded from the sample</td>
</tr>
<tr>
<td>size-fraction upper threshold (<a href="../0000736/">size_frac_up</a>)</td>
<td>Mesh or pore size of the device used to retain the sample. Materials smaller than the size threshold are excluded from the sample</td>
</tr>
<tr>
<td>slope aspect (<a href="../0000647/">slope_aspect</a>)</td>
<td>The direction a slope faces. While looking down a slope use a compass to record the direction you are facing (direction or degrees); e.g., nw or 315 degrees. This measure provides an indication of sun and wind exposure that will influence soil temperature and evapotranspiration</td>
</tr>
<tr>
<td>slope gradient (<a href="../0000646/">slope_gradient</a>)</td>
<td>Commonly called 'slope'. The angle between ground surface and a horizontal line (in percent). This is the direction that overland water would flow. This measure is usually taken with a hand level meter or clinometer</td>
</tr>
<tr>
<td>sludge retention time (<a href="../0000669/">sludge_retent_time</a>)</td>
<td>The time activated sludge remains in reactor</td>
</tr>
<tr>
<td>smoker (<a href="../0000262/">smoker</a>)</td>
<td>Specification of smoking status</td>
</tr>
<tr>
<td>sodium (<a href="../0000428/">sodium</a>)</td>
<td>Sodium concentration in the sample</td>
</tr>
<tr>
<td>soil conductivity (<a href="../0001158/">soil_conductivity</a>)</td>
<td>None</td>
</tr>
<tr>
<td>soil cover (<a href="../0001159/">soil_cover</a>)</td>
<td>Material covering the sampled soil. This field accepts terms under ENVO:00010483, environmental material</td>
</tr>
<tr>
<td>soil horizon (<a href="../0001082/">soil_horizon</a>)</td>
<td>Specific layer in the land area which measures parallel to the soil surface and possesses physical characteristics which differ from the layers above and beneath</td>
</tr>
<tr>
<td>soil pH (<a href="../0001160/">soil_pH</a>)</td>
<td>None</td>
</tr>
<tr>
<td>soil sediment porosity (<a href="../0001162/">soil_porosity</a>)</td>
<td>Porosity of soil or deposited sediment is volume of voids divided by the total volume of sample</td>
</tr>
<tr>
<td>soil temperature (<a href="../0001163/">soil_temp</a>)</td>
<td>Temperature of soil at the time of sampling</td>
</tr>
<tr>
<td>soil texture (<a href="../0000335/">soil_texture</a>)</td>
<td>The relative proportion of different grain sizes of mineral particles in a soil, as described using a standard system; express as % sand (50 um to 2 mm), silt (2 um to 50 um), and clay (&lt;2 um) with textural name (e.g., silty clay loam) optional</td>
</tr>
<tr>
<td>soil texture classification (<a href="../0001164/">soil_texture_class</a>)</td>
<td>One of the 12 soil texture classes use to describe soil texture based on the relative proportion of different grain sizes  of mineral particles [sand (50 um to 2 mm), silt (2 um to 50 um), and clay (&lt;2 um)] in a soil</td>
</tr>
<tr>
<td>soil texture method (<a href="../0000336/">soil_texture_meth</a>)</td>
<td>Reference or method used in determining soil texture</td>
</tr>
<tr>
<td>soil type (<a href="../0000332/">soil_type</a>)</td>
<td>Description of the soil type or classification. This field accepts terms under soil (<a href="http://purl.obolibrary.org/obo/ENVO_00001998">http://purl.obolibrary.org/obo/ENVO_00001998</a>).  Multiple terms can be separated by pipes</td>
</tr>
<tr>
<td>soil type method (<a href="../0000334/">soil_type_meth</a>)</td>
<td>Reference or method used in determining soil series name or other lower-level classification</td>
</tr>
<tr>
<td>solar irradiance (<a href="../0000112/">solar_irradiance</a>)</td>
<td>The amount of solar energy that arrives at a specific area of a surface during a specific time interval</td>
</tr>
<tr>
<td>soluble inorganic material (<a href="../0000672/">soluble_inorg_mat</a>)</td>
<td>Concentration of substances such as ammonia, road-salt, sea-salt, cyanide, hydrogen sulfide, thiocyanates, thiosulfates, etc</td>
</tr>
<tr>
<td>soluble organic material (<a href="../0000673/">soluble_org_mat</a>)</td>
<td>Concentration of substances such as urea, fruit sugars, soluble proteins, drugs, pharmaceuticals, etc</td>
</tr>
<tr>
<td>soluble reactive phosphorus (<a href="../0000738/">soluble_react_phosp</a>)</td>
<td>Concentration of soluble reactive phosphorus</td>
</tr>
<tr>
<td>relevant standard operating procedures (<a href="../0000090/">sop</a>)</td>
<td>Standard operating procedures used in assembly and/or annotation of genomes, metagenomes or environmental sequences</td>
</tr>
<tr>
<td>sorting technology (<a href="../0000075/">sort_tech</a>)</td>
<td>Method used to sort/isolate cells or particles of interest</td>
</tr>
<tr>
<td>source material identifiers (<a href="../0000026/">source_mat_id</a>)</td>
<td>A unique identifier assigned to a material sample (as defined by <a href="http://rs.tdwg.org/dwc/terms/materialSampleID">http://rs.tdwg.org/dwc/terms/materialSampleID</a>, and as opposed to a particular digital record of a material sample) used for extracting nucleic acids, and subsequent sequencing. The identifier can refer either to the original material collected or to any derived sub-samples. The INSDC qualifiers /specimen_voucher, /bio_material, or /culture_collection may or may not share the same value as the source_mat_id field. For instance, the /specimen_voucher qualifier and source_mat_id may both contain 'UAM:Herps:14' , referring to both the specimen voucher and sampled tissue with the same identifier. However, the /culture_collection qualifier may refer to a value from an initial culture (e.g. ATCC:11775) while source_mat_id would refer to an identifier from some derived culture from which the nucleic acids were extracted (e.g. xatc123 or ark:/2154/R2)</td>
</tr>
<tr>
<td>source of UViGs (<a href="../0000035/">source_uvig</a>)</td>
<td>Type of dataset from which the UViG was obtained</td>
</tr>
<tr>
<td>space typical state (<a href="../0000770/">space_typ_state</a>)</td>
<td>Customary or normal state of the space</td>
</tr>
<tr>
<td>specific intended consumer (<a href="../0001234/">spec_intended_cons</a>)</td>
<td>Food consumer type, human or animal, for which the food product is produced and marketed. This field accepts terms listed under food consumer group (<a href="http://purl.obolibrary.org/obo/FOODON_03510136">http://purl.obolibrary.org/obo/FOODON_03510136</a>)</td>
</tr>
<tr>
<td>special diet (<a href="../0000905/">special_diet</a>)</td>
<td>Specification of special diet; can include multiple special diets</td>
</tr>
<tr>
<td>specifications (<a href="../0000836/">specific</a>)</td>
<td>The building specifications. If design is chosen, indicate phase: conceptual, schematic, design development, construction documents</td>
</tr>
<tr>
<td>host scientific name (<a href="../0000029/">specific_host</a>)</td>
<td>Report the host's taxonomic name and/or NCBI taxonomy ID</td>
</tr>
<tr>
<td>specific humidity (<a href="../0000214/">specific_humidity</a>)</td>
<td>The mass of water vapour in a unit mass of moist air, usually expressed as grams of vapour per kilogram of air, or, in air conditioning, as grains per pound</td>
</tr>
<tr>
<td>antimicrobial phenotype of spike-in bacteria (<a href="../0001235/">spikein_AMR</a>)</td>
<td>Qualitative description of a microbial response to antimicrobial agents. Bacteria may be susceptible or resistant to a broad range of antibiotic drugs or drug classes, with several intermediate states or phases. This field accepts terms under antimicrobial phenotype (<a href="http://purl.obolibrary.org/obo/ARO_3004299">http://purl.obolibrary.org/obo/ARO_3004299</a>)</td>
</tr>
<tr>
<td>spike-in with antibiotics (<a href="../0001171/">spikein_antibiotic</a>)</td>
<td>Antimicrobials used in research study to assess effects of exposure on microbiome of a specific site.  Please list antimicrobial, common name and/or class and concentration used for spike-in</td>
</tr>
<tr>
<td>spike-in organism count (<a href="../0001335/">spikein_count</a>)</td>
<td>Total cell count of any organism (or group of organisms) per gram, volume or area of sample, should include name of organism followed by count. The method that was used for the enumeration (e.g. qPCR, atp, mpn, etc.) should also be provided (example: total prokaryotes; 3.5e7 cells per ml; qPCR)</td>
</tr>
<tr>
<td>spike-in growth medium (<a href="../0001169/">spikein_growth_med</a>)</td>
<td>A liquid or gel containing nutrients, salts, and other factors formulated to support the growth of microorganisms, cells, or plants (National Cancer Institute Thesaurus).  A growth medium is a culture medium which has the disposition to encourage growth of particular bacteria to the exclusion of others in the same growth environment.  In this case, list the culture medium used to propagate the spike-in bacteria during preparation of spike-in inoculum. This field accepts terms listed under microbiological culture medium (<a href="http://purl.obolibrary.org/obo/MICRO_0000067">http://purl.obolibrary.org/obo/MICRO_0000067</a>). If the proper descriptor is not listed please use text to describe the spike in growth media</td>
</tr>
<tr>
<td>spike-in with heavy metals (<a href="../0001172/">spikein_metal</a>)</td>
<td>Heavy metals used in research study to assess effects of exposure on microbiome of a specific site.  Please list heavy metals and concentration used for spike-in</td>
</tr>
<tr>
<td>spike in organism (<a href="../0001167/">spikein_org</a>)</td>
<td>Taxonomic information about the spike-in organism(s). This field accepts terms under organism (<a href="http://purl.obolibrary.org/obo/NCIT_C14250">http://purl.obolibrary.org/obo/NCIT_C14250</a>). This field also accepts identification numbers from NCBI under <a href="https://www.ncbi.nlm.nih.gov/taxonomy">https://www.ncbi.nlm.nih.gov/taxonomy</a>. Multiple terms can be separated by pipes</td>
</tr>
<tr>
<td>spike-in bacterial serovar or serotype (<a href="../0001168/">spikein_serovar</a>)</td>
<td>Taxonomic information about the spike-in organism(s) at the serovar or serotype level. This field accepts terms under organism (<a href="http://purl.obolibrary.org/obo/NCIT_C14250">http://purl.obolibrary.org/obo/NCIT_C14250</a>). This field also accepts identification numbers from NCBI under <a href="https://www.ncbi.nlm.nih.gov/taxonomy">https://www.ncbi.nlm.nih.gov/taxonomy</a>. Multiple terms can be separated by pipes</td>
</tr>
<tr>
<td>spike-in microbial strain (<a href="../0001170/">spikein_strain</a>)</td>
<td>Taxonomic information about the spike-in organism(s) at the strain level. This field accepts terms under organism (<a href="http://purl.obolibrary.org/obo/NCIT_C14250">http://purl.obolibrary.org/obo/NCIT_C14250</a>). This field also accepts identification numbers from NCBI under <a href="https://www.ncbi.nlm.nih.gov/taxonomy">https://www.ncbi.nlm.nih.gov/taxonomy</a>. Multiple terms can be separated by pipes</td>
</tr>
<tr>
<td>source rock depositional environment (<a href="../0000996/">sr_dep_env</a>)</td>
<td>Source rock depositional environment (<a href="https://en.wikipedia.org/wiki/Source_rock">https://en.wikipedia.org/wiki/Source_rock</a>). If "other" is specified, please propose entry in "additional info" field</td>
</tr>
<tr>
<td>source rock geological age (<a href="../0000997/">sr_geol_age</a>)</td>
<td>Geological age of source rock (Additional info: <a href="https://en.wikipedia.org/wiki/Period_(geology">https://en.wikipedia.org/wiki/Period_(geology</a>)). If "other" is specified, please propose entry in "additional info" field</td>
</tr>
<tr>
<td>source rock kerogen type (<a href="../0000994/">sr_kerog_type</a>)</td>
<td>Origin of kerogen. Type I: Algal (aquatic), Type II: planktonic and soft plant material (aquatic or terrestrial), Type III: terrestrial woody/ fibrous plant material (terrestrial), Type IV: oxidized recycled woody debris (terrestrial) (additional information: <a href="https://en.wikipedia.org/wiki/Kerogen">https://en.wikipedia.org/wiki/Kerogen</a>). If "other" is specified, please propose entry in "additional info" field</td>
</tr>
<tr>
<td>source rock lithology (<a href="../0000995/">sr_lithology</a>)</td>
<td>Lithology of source rock (<a href="https://en.wikipedia.org/wiki/Source_rock">https://en.wikipedia.org/wiki/Source_rock</a>). If "other" is specified, please propose entry in "additional info" field</td>
</tr>
<tr>
<td>standing water regimen (<a href="../0001069/">standing_water_regm</a>)</td>
<td>Treatment involving an exposure to standing water during a plant's life span, types can be flood water or standing water, treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include multiple regimens</td>
</tr>
<tr>
<td>sampling room sterilization method (<a href="../0001259/">ster_meth_samp_room</a>)</td>
<td>The method used to sterilize the sampling room. This field accepts terms listed under electromagnetic radiation (<a href="http://purl.obolibrary.org/obo/ENVO_01001026">http://purl.obolibrary.org/obo/ENVO_01001026</a>). If the proper descriptor is not listed, please use text to describe the sampling room sterilization method. Multiple terms can be separated by pipes</td>
</tr>
<tr>
<td>storage conditions (<a href="../0000327/">store_cond</a>)</td>
<td>Explain how and for how long the soil sample was stored before DNA extraction (fresh/frozen/other)</td>
</tr>
<tr>
<td>study completion status (<a href="../0000898/">study_complt_stat</a>)</td>
<td>Specification of study completion status, if no the reason should be specified</td>
</tr>
<tr>
<td>study design (<a href="../0001236/">study_design</a>)</td>
<td>A plan specification comprised of protocols (which may specify how and what kinds of data will be gathered) that are executed as part of an investigation and is realized during a study design execution. This field accepts terms under study design (<a href="http://purl.obolibrary.org/obo/OBI_0500000">http://purl.obolibrary.org/obo/OBI_0500000</a>). If the proper descriptor is not listed please use text to describe the study design. Multiple terms can be separated by pipes</td>
</tr>
<tr>
<td>study incubation duration (<a href="../0001237/">study_inc_dur</a>)</td>
<td>Sample incubation duration if unpublished or unvalidated method is used. Indicate the timepoint written in ISO 8601 format</td>
</tr>
<tr>
<td>study incubation temperature (<a href="../0001238/">study_inc_temp</a>)</td>
<td>Sample incubation temperature if unpublished or unvalidated method is used</td>
</tr>
<tr>
<td>time-course duration (<a href="../0001239/">study_timecourse</a>)</td>
<td>For time-course research studies involving samples of the food commodity, indicate the total duration of the time-course study</td>
</tr>
<tr>
<td>study treatment (<a href="../0001240/">study_tmnt</a>)</td>
<td>A process in which the act is intended to modify or alter some other material entity.  From the study design, each treatment is comprised of one level of one or multiple factors. This field accepts terms listed under treatment (<a href="http://purl.obolibrary.org/obo/MCO_0000866">http://purl.obolibrary.org/obo/MCO_0000866</a>). If the proper descriptor is not listed please use text to describe the study treatment. Multiple terms can be separated by one or more pipes</td>
</tr>
<tr>
<td>subspecific genetic lineage (<a href="../0000020/">subspecf_gen_lin</a>)</td>
<td>Information about the genetic distinctness of the sequenced organism below the subspecies level, e.g., serovar, serotype, biotype, ecotype, or any relevant genetic typing schemes like Group I plasmid. Subspecies should not be recorded in this term, but in the NCBI taxonomy. Supply both the lineage name and the lineage rank separated by a colon, e.g., biovar:abc123</td>
</tr>
<tr>
<td>substructure type (<a href="../0000767/">substructure_type</a>)</td>
<td>The substructure or under building is that largely hidden section of the building which is built off the foundations to the ground floor level</td>
</tr>
<tr>
<td>sulfate (<a href="../0000423/">sulfate</a>)</td>
<td>Concentration of sulfate in the sample</td>
</tr>
<tr>
<td>sulfate in formation water (<a href="../0000407/">sulfate_fw</a>)</td>
<td>Original sulfate concentration in the hydrocarbon resource</td>
</tr>
<tr>
<td>sulfide (<a href="../0000424/">sulfide</a>)</td>
<td>Concentration of sulfide in the sample</td>
</tr>
<tr>
<td>surface-air contaminant (<a href="../0000759/">surf_air_cont</a>)</td>
<td>Contaminant identified on surface</td>
</tr>
<tr>
<td>surface humidity (<a href="../0000123/">surf_humidity</a>)</td>
<td>Surfaces: water activity as a function of air and material moisture</td>
</tr>
<tr>
<td>surface material (<a href="../0000758/">surf_material</a>)</td>
<td>Surface materials at the point of sampling</td>
</tr>
<tr>
<td>surface moisture (<a href="../0000128/">surf_moisture</a>)</td>
<td>Water held on a surface</td>
</tr>
<tr>
<td>surface moisture pH (<a href="../0000760/">surf_moisture_ph</a>)</td>
<td>ph measurement of surface</td>
</tr>
<tr>
<td>surface temperature (<a href="../0000125/">surf_temp</a>)</td>
<td>Temperature of the surface at the time of sampling</td>
</tr>
<tr>
<td>suspended particulate matter (<a href="../0000741/">suspend_part_matter</a>)</td>
<td>Concentration of suspended particulate matter</td>
</tr>
<tr>
<td>suspended solids (<a href="../0000150/">suspend_solids</a>)</td>
<td>Concentration of substances including a wide variety of material, such as silt, decaying plant and animal matter; can include multiple substances</td>
</tr>
<tr>
<td>symbiotic host organism life cycle type (<a href="../0001300/">sym_life_cycle_type</a>)</td>
<td>Type of life cycle of the symbiotic host species (the thing being sampled). Simple life cycles occur within a single host, complex ones within multiple different hosts over the course of their normal life cycle</td>
</tr>
<tr>
<td>host of the symbiont role (<a href="../0001303/">symbiont_host_role</a>)</td>
<td>Role of the host in the life cycle of the symbiotic organism</td>
</tr>
<tr>
<td>total acid number (<a href="../0000120/">tan</a>)</td>
<td>Total Acid Number  (TAN) is a measurement of acidity that is determined by the amount of  potassium hydroxide  in milligrams that is needed to neutralize the acids in one gram of oil.  It is an important quality measurement of  crude oil. (source: <a href="https://en.wikipedia.org/wiki/Total_acid_number">https://en.wikipedia.org/wiki/Total_acid_number</a>)</td>
</tr>
<tr>
<td>target gene (<a href="../0000044/">target_gene</a>)</td>
<td>Targeted gene or locus name for marker gene studies</td>
</tr>
<tr>
<td>target subfragment (<a href="../0000045/">target_subfragment</a>)</td>
<td>Name of subfragment of a gene or locus. Important to e.g. identify special regions on marker genes like V6 on 16S rRNA</td>
</tr>
<tr>
<td>taxonomic classification (<a href="../0000064/">tax_class</a>)</td>
<td>Method used for taxonomic classification, along with reference database used, classification rank, and thresholds used to classify new genomes</td>
</tr>
<tr>
<td>taxonomic identity marker (<a href="../0000053/">tax_ident</a>)</td>
<td>The phylogenetic marker(s) used to assign an organism name to the SAG or MAG</td>
</tr>
<tr>
<td>temperature (<a href="../0000113/">temp</a>)</td>
<td>Temperature of the sample at the time of sampling</td>
</tr>
<tr>
<td>temperature outside house (<a href="../0000197/">temp_out</a>)</td>
<td>The recorded temperature value at sampling time outside</td>
</tr>
<tr>
<td>tertiary treatment (<a href="../0000352/">tertiary_treatment</a>)</td>
<td>The process providing a final treatment stage to raise the effluent quality before it is discharged to the receiving environment</td>
</tr>
<tr>
<td>tidal stage (<a href="../0000750/">tidal_stage</a>)</td>
<td>Stage of tide</td>
</tr>
<tr>
<td>history/tillage (<a href="../0001081/">tillage</a>)</td>
<td>Note method(s) used for tilling</td>
</tr>
<tr>
<td>time since last toothbrushing (<a href="../0000924/">time_last_toothbrush</a>)</td>
<td>Specification of the time since last toothbrushing</td>
</tr>
<tr>
<td>time since last wash (<a href="../0000943/">time_since_last_wash</a>)</td>
<td>Specification of the time since last wash</td>
</tr>
<tr>
<td>timepoint (<a href="../0001173/">timepoint</a>)</td>
<td>Time point at which a sample or observation is made or taken from a biomaterial as measured from some reference point. Indicate the timepoint written in ISO 8601 format</td>
</tr>
<tr>
<td>tissue culture growth media (<a href="../0001070/">tiss_cult_growth_med</a>)</td>
<td>Description of plant tissue culture growth media used</td>
</tr>
<tr>
<td>toluene (<a href="../0000154/">toluene</a>)</td>
<td>Concentration of toluene in the sample</td>
</tr>
<tr>
<td>total carbon (<a href="../0000525/">tot_carb</a>)</td>
<td>Total carbon content</td>
</tr>
<tr>
<td>total depth of water column (<a href="../0000634/">tot_depth_water_col</a>)</td>
<td>Measurement of total depth of water column</td>
</tr>
<tr>
<td>total dissolved nitrogen (<a href="../0000744/">tot_diss_nitro</a>)</td>
<td>Total dissolved nitrogen concentration, reported as nitrogen, measured by: total dissolved nitrogen = NH4 + NO3NO2 + dissolved organic nitrogen</td>
</tr>
<tr>
<td>total inorganic nitrogen (<a href="../0000745/">tot_inorg_nitro</a>)</td>
<td>Total inorganic nitrogen content</td>
</tr>
<tr>
<td>total iron (<a href="../0000105/">tot_iron</a>)</td>
<td>Concentration of total iron in the sample</td>
</tr>
<tr>
<td>total nitrogen concentration (<a href="../0000102/">tot_nitro</a>)</td>
<td>Total nitrogen concentration of water samples, calculated by: total nitrogen = total dissolved nitrogen + particulate nitrogen. Can also be measured without filtering, reported as nitrogen</td>
</tr>
<tr>
<td>total nitrogen content method (<a href="../0000338/">tot_nitro_cont_meth</a>)</td>
<td>Reference or method used in determining the total nitrogen</td>
</tr>
<tr>
<td>total nitrogen content (<a href="../0000530/">tot_nitro_content</a>)</td>
<td>Total nitrogen content of the sample</td>
</tr>
<tr>
<td>total organic carbon method (<a href="../0000337/">tot_org_c_meth</a>)</td>
<td>Reference or method used in determining total organic carbon</td>
</tr>
<tr>
<td>total organic carbon (<a href="../0000533/">tot_org_carb</a>)</td>
<td>Total organic carbon content</td>
</tr>
<tr>
<td>total particulate carbon (<a href="../0000747/">tot_part_carb</a>)</td>
<td>Total particulate carbon content</td>
</tr>
<tr>
<td>total phosphorus (<a href="../0000117/">tot_phosp</a>)</td>
<td>Total phosphorus concentration in the sample, calculated by: total phosphorus = total dissolved phosphorus + particulate phosphorus</td>
</tr>
<tr>
<td>total phosphate (<a href="../0000689/">tot_phosphate</a>)</td>
<td>Total amount or concentration of phosphate</td>
</tr>
<tr>
<td>total sulfur (<a href="../0000419/">tot_sulfur</a>)</td>
<td>Concentration of total sulfur in the sample</td>
</tr>
<tr>
<td>train line (<a href="../0000837/">train_line</a>)</td>
<td>The subway line name</td>
</tr>
<tr>
<td>train station collection location (<a href="../0000838/">train_stat_loc</a>)</td>
<td>The train station collection location</td>
</tr>
<tr>
<td>train stop collection location (<a href="../0000839/">train_stop_loc</a>)</td>
<td>The train stop collection location</td>
</tr>
<tr>
<td>travel outside the country in last six months (<a href="../0000268/">travel_out_six_month</a>)</td>
<td>Specification of the countries travelled in the last six months; can include multiple travels</td>
</tr>
<tr>
<td>tRNA extraction software (<a href="../0000068/">trna_ext_software</a>)</td>
<td>Tools used for tRNA identification</td>
</tr>
<tr>
<td>number of standard tRNAs extracted (<a href="../0000067/">trnas</a>)</td>
<td>The total number of tRNAs identified from the SAG or MAG</td>
</tr>
<tr>
<td>trophic level (<a href="../0000032/">trophic_level</a>)</td>
<td>Trophic levels are the feeding position in a food chain. Microbes can be a range of producers (e.g. chemolithotroph)</td>
</tr>
<tr>
<td>turbidity (<a href="../0000191/">turbidity</a>)</td>
<td>Measure of the amount of cloudiness or haziness in water caused by individual particles</td>
</tr>
<tr>
<td>depth (TVDSS) of hydrocarbon resource pressure (<a href="../0000397/">tvdss_of_hcr_press</a>)</td>
<td>True vertical depth subsea (TVDSS) of the hydrocarbon resource where the original pressure was measured (e.g. 1578 m)</td>
</tr>
<tr>
<td>depth (TVDSS) of hydrocarbon resource temperature (<a href="../0000394/">tvdss_of_hcr_temp</a>)</td>
<td>True vertical depth subsea (TVDSS) of the hydrocarbon resource where the original temperature was measured (e.g. 1345 m)</td>
</tr>
<tr>
<td>twin sibling presence (<a href="../0000326/">twin_sibling</a>)</td>
<td>Specification of twin sibling presence</td>
</tr>
<tr>
<td>typical occupant density (<a href="../0000771/">typ_occup_density</a>)</td>
<td>Customary or normal density of occupants</td>
</tr>
<tr>
<td>type of symbiosis (<a href="../0001307/">type_of_symbiosis</a>)</td>
<td>Type of biological interaction established between the symbiotic host organism being sampled and its respective host</td>
</tr>
<tr>
<td>urine/collection method (<a href="../0000899/">urine_collect_meth</a>)</td>
<td>Specification of urine collection method</td>
</tr>
<tr>
<td>host sex (<a href="../0000862/">urobiom_sex</a>)</td>
<td>Physical sex of the host</td>
</tr>
<tr>
<td>urogenital disorder (<a href="../0000289/">urogenit_disord</a>)</td>
<td>History of urogenital disorders, can include multiple disorders. The terms should be chosen from the DO (Human Disease Ontology) at <a href="http://www.disease-ontology.org">http://www.disease-ontology.org</a>, reproductive system disease (<a href="https://disease-ontology.org/?id=DOID:15">https://disease-ontology.org/?id=DOID:15</a>) or urinary system disease (<a href="https://disease-ontology.org/?id=DOID:18">https://disease-ontology.org/?id=DOID:18</a>)</td>
</tr>
<tr>
<td>urine/urogenital tract disorder (<a href="../0000278/">urogenit_tract_disor</a>)</td>
<td>History of urogenital tract disorders; can include multiple disorders. The terms should be chosen from the DO (Human Disease Ontology) at <a href="http://www.disease-ontology.org">http://www.disease-ontology.org</a>, urinary system disease (<a href="https://disease-ontology.org/?id=DOID:18">https://disease-ontology.org/?id=DOID:18</a>)</td>
</tr>
<tr>
<td>ventilation rate (<a href="../0000114/">ventilation_rate</a>)</td>
<td>Ventilation rate of the system in the sampled premises</td>
</tr>
<tr>
<td>ventilation type (<a href="../0000756/">ventilation_type</a>)</td>
<td>Ventilation system used in the sampled premises</td>
</tr>
<tr>
<td>volatile fatty acids (<a href="../0000152/">vfa</a>)</td>
<td>Concentration of Volatile Fatty Acids in the sample</td>
</tr>
<tr>
<td>vfa in formation water (<a href="../0000408/">vfa_fw</a>)</td>
<td>Original volatile fatty acid concentration in the hydrocarbon resource</td>
</tr>
<tr>
<td>viral identification software (<a href="../0000081/">vir_ident_software</a>)</td>
<td>Tool(s) used for the identification of UViG as a viral genome, software or protocol name including version number, parameters, and cutoffs used</td>
</tr>
<tr>
<td>virus enrichment approach (<a href="../0000036/">virus_enrich_appr</a>)</td>
<td>List of approaches used to enrich the sample for viruses, if any</td>
</tr>
<tr>
<td>visual media (<a href="../0000840/">vis_media</a>)</td>
<td>The building visual media</td>
</tr>
<tr>
<td>viscosity (<a href="../0000126/">viscosity</a>)</td>
<td>A measure of oil's resistance  to gradual deformation by  shear stress  or  tensile stress (e.g. 3.5 cp; 100   C)</td>
</tr>
<tr>
<td>volatile organic compounds (<a href="../0000115/">volatile_org_comp</a>)</td>
<td>Concentration of carbon-based chemicals that easily evaporate at room temperature; can report multiple volatile organic compounds by entering numeric values preceded by name of compound</td>
</tr>
<tr>
<td>wall area (<a href="../0000198/">wall_area</a>)</td>
<td>The total area of the sampled room's walls</td>
</tr>
<tr>
<td>wall construction type (<a href="../0000841/">wall_const_type</a>)</td>
<td>The building class of the wall defined by the composition of the building elements and fire-resistance rating</td>
</tr>
<tr>
<td>wall finish material (<a href="../0000842/">wall_finish_mat</a>)</td>
<td>The material utilized to finish the outer most layer of the wall</td>
</tr>
<tr>
<td>wall height (<a href="../0000221/">wall_height</a>)</td>
<td>The average height of the walls in the sampled room</td>
</tr>
<tr>
<td>wall location (<a href="../0000843/">wall_loc</a>)</td>
<td>The relative location of the wall within the room</td>
</tr>
<tr>
<td>wall surface treatment (<a href="../0000845/">wall_surf_treatment</a>)</td>
<td>The surface treatment of interior wall</td>
</tr>
<tr>
<td>wall texture (<a href="../0000846/">wall_texture</a>)</td>
<td>The feel, appearance, or consistency of a wall surface</td>
</tr>
<tr>
<td>wall thermal mass (<a href="../0000222/">wall_thermal_mass</a>)</td>
<td>The ability of the wall to provide inertia against temperature fluctuations. Generally this means concrete or concrete block that is either exposed or covered only with paint</td>
</tr>
<tr>
<td>wall signs of water/mold (<a href="../0000844/">wall_water_mold</a>)</td>
<td>Signs of the presence of mold or mildew on a wall</td>
</tr>
<tr>
<td>wastewater type (<a href="../0000353/">wastewater_type</a>)</td>
<td>The origin of wastewater such as human waste, rainfall, storm drains, etc</td>
</tr>
<tr>
<td>water content method (<a href="../0000323/">water_cont_soil_meth</a>)</td>
<td>Reference or method used in determining the water content of soil</td>
</tr>
<tr>
<td>water content (<a href="../0000185/">water_content</a>)</td>
<td>Water content measurement</td>
</tr>
<tr>
<td>water current (<a href="../0000203/">water_current</a>)</td>
<td>Measurement of magnitude and direction of flow within a fluid</td>
</tr>
<tr>
<td>water cut (<a href="../0000454/">water_cut</a>)</td>
<td>Current amount of water (%) in a produced fluid stream; or the average of the combined streams</td>
</tr>
<tr>
<td>water feature size (<a href="../0000223/">water_feat_size</a>)</td>
<td>The size of the water feature</td>
</tr>
<tr>
<td>water feature type (<a href="../0000847/">water_feat_type</a>)</td>
<td>The type of water feature present within the building being sampled</td>
</tr>
<tr>
<td>water delivery frequency (<a href="../0001174/">water_frequency</a>)</td>
<td>Number of water delivery events within a given period of time</td>
</tr>
<tr>
<td>water pH (<a href="../0001175/">water_pH</a>)</td>
<td>None</td>
</tr>
<tr>
<td>water production rate (<a href="../0000453/">water_prod_rate</a>)</td>
<td>Water production rates per well (e.g. 987 m3 / day)</td>
</tr>
<tr>
<td>environmental feature adjacent water source (<a href="../0001122/">water_source_adjac</a>)</td>
<td>Description of the environmental features that are adjacent to the farm water source. This field accepts terms under ecosystem (<a href="http://purl.obolibrary.org/obo/ENVO_01001110">http://purl.obolibrary.org/obo/ENVO_01001110</a>) and human construction (<a href="http://purl.obolibrary.org/obo/ENVO_00000070">http://purl.obolibrary.org/obo/ENVO_00000070</a>). Multiple terms can be separated by pipes</td>
</tr>
<tr>
<td>water source shared (<a href="../0001176/">water_source_shared</a>)</td>
<td>Other users sharing access to the same water source. Multiple terms can be separated by one or more pipes</td>
</tr>
<tr>
<td>water temperature regimen (<a href="../0000590/">water_temp_regm</a>)</td>
<td>Information about treatment involving an exposure to water with varying degree of temperature, treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include multiple regimens</td>
</tr>
<tr>
<td>watering regimen (<a href="../0000591/">watering_regm</a>)</td>
<td>Information about treatment involving an exposure to watering frequencies, treatment regimen including how many times the treatment was repeated, how long each treatment lasted, and the start and end time of the entire treatment; can include multiple regimens</td>
</tr>
<tr>
<td>weekday (<a href="../0000848/">weekday</a>)</td>
<td>The day of the week when sampling occurred</td>
</tr>
<tr>
<td>weight loss in last three months (<a href="../0000295/">weight_loss_3_month</a>)</td>
<td>Specification of weight loss in the last three months, if yes should be further specified to include amount of weight loss</td>
</tr>
<tr>
<td>WGA amplification approach (<a href="../0000055/">wga_amp_appr</a>)</td>
<td>Method used to amplify genomic DNA in preparation for sequencing</td>
</tr>
<tr>
<td>WGA amplification kit (<a href="../0000006/">wga_amp_kit</a>)</td>
<td>Kit used to amplify genomic DNA in preparation for sequencing</td>
</tr>
<tr>
<td>well identification number (<a href="../0000297/">win</a>)</td>
<td>A unique identifier of a well or wellbore. This is part of the Global Framework for Well Identification initiative which is compiled by the Professional Petroleum Data Management Association (PPDM) in an effort to improve well identification systems. (Supporting information: <a href="https://ppdm.org/">https://ppdm.org/</a> and <a href="http://dl.ppdm.org/dl/690">http://dl.ppdm.org/dl/690</a>)</td>
</tr>
<tr>
<td>wind direction (<a href="../0000757/">wind_direction</a>)</td>
<td>Wind direction is the direction from which a wind originates</td>
</tr>
<tr>
<td>wind speed (<a href="../0000118/">wind_speed</a>)</td>
<td>speed of wind measured at the time of sampling</td>
</tr>
<tr>
<td>window condition (<a href="../0000849/">window_cond</a>)</td>
<td>The physical condition of the window at the time of sampling</td>
</tr>
<tr>
<td>window covering (<a href="../0000850/">window_cover</a>)</td>
<td>The type of window covering</td>
</tr>
<tr>
<td>window horizontal position (<a href="../0000851/">window_horiz_pos</a>)</td>
<td>The horizontal position of the window on the wall</td>
</tr>
<tr>
<td>window location (<a href="../0000852/">window_loc</a>)</td>
<td>The relative location of the window within the room</td>
</tr>
<tr>
<td>window material (<a href="../0000853/">window_mat</a>)</td>
<td>The type of material used to finish a window</td>
</tr>
<tr>
<td>window open frequency (<a href="../0000246/">window_open_freq</a>)</td>
<td>The number of times windows are opened per week</td>
</tr>
<tr>
<td>window area/size (<a href="../0000224/">window_size</a>)</td>
<td>The window's length and width</td>
</tr>
<tr>
<td>window status (<a href="../0000855/">window_status</a>)</td>
<td>Defines whether the windows were open or closed during environmental testing</td>
</tr>
<tr>
<td>window type (<a href="../0000856/">window_type</a>)</td>
<td>The type of windows</td>
</tr>
<tr>
<td>window vertical position (<a href="../0000857/">window_vert_pos</a>)</td>
<td>The vertical position of the window on the wall</td>
</tr>
<tr>
<td>window signs of water/mold (<a href="../0000854/">window_water_mold</a>)</td>
<td>Signs of the presence of mold or mildew on the window</td>
</tr>
<tr>
<td>16S recovered (<a href="../0000065/">x16s_recover</a>)</td>
<td>Can a 16S gene be recovered from the submitted SAG or MAG?</td>
</tr>
<tr>
<td>16S recovery software (<a href="../0000066/">x16s_recover_software</a>)</td>
<td>Tools used for 16S rRNA gene extraction</td>
</tr>
<tr>
<td>xylene (<a href="../0000156/">xylene</a>)</td>
<td>Concentration of xylene in the sample</td>
</tr>
</tbody>
</table>
"""
    soup = BeautifulSoup(html, "html.parser")
    a_href = soup.find_all('a')

    mixs_fields_uri_lst = dict()

    for x in a_href:
        href= x['href']
        element = x.text
        
        if "../" in href:
            data= dict()
            mixs_field = element
            suffix = href[href.find("../")+1:href.find('/">')][2::]
            uri = f'https://genomicsstandardsconsortium.github.io/mixs/{suffix}'
            data[mixs_field] = {"uri": uri}

            mixs_fields_uri_lst.update(data)
    return mixs_fields_uri_lst

def generate_mixs_fields_json():
    out = list()
    mixs_json = list()

    # Get MiXS json schema from GitHub
    mixs_json_schema_url =  "https://raw.githubusercontent.com/GenomicsStandardsConsortium/mixs/main/project/jsonschema/mixs.schema.json"

    try:
        # Read the json schema from the URL and load the json file
        resp = requests.get(mixs_json_schema_url)
        mixs_json_file = json.loads(resp.text)

        # Remove the $defs key from the dictionary
        # and create a list of dictionaries
        mixs_dict_def = mixs_json_file.get('$defs','')
        
        # Rearrange the list of dictionaries and retrieve only the 
        # field name, 'description', 'type' and 'pattern' keys from the MIxS json
        # NB: 'pattern' in the json schema is known as 'regex' in the TOL schema
        data = dict()
        #mixs_json = [{'field':key, 'type': value_dict.get('type',''), 'regex': value_dict.get('pattern',''), 'description': value_dict.get('description','')} for key, value_dict in mixs_dict_def.items()]
        
        for key, value_dict in mixs_dict_def.items():
            if not value_dict.get('properties',''):
                data = {'field':key, 'type': value_dict.get('type',''), 'regex': value_dict.get('pattern',''), 'description': value_dict.get('description','')}
                
                mixs_json.append(data)

            if value_dict.get('properties',''):
                for k, v in value_dict.get('properties','').items():
                    data = {'field':k, 'type': v.get('type',''), 'regex': v.get('pattern',''), 'description': v.get('description','')}
            
                    mixs_json.append(data)
        
        # Remove duplicates from the json file
        mixs_json = list(remove_duplicates_from_json(mixs_json))

        # Uncomment the following lines to generate the MIxS json schema to a file
        # in the '/copo/common/schema_versions/isa_mappings/' directory
        '''
        file_name = "mixs_fields.json"
        file_directory = "/copo/common/schema_versions/isa_mappings/"
        file_path = file_directory + file_name

        with open(file_path, 'w+') as f:
            print(json.dumps(mixs_json, indent=4, sort_keys=False,default=str), file=f)
            f.close()
        '''

        out = mixs_json
        
    except Exception as e:
        print(f'Error: {e}')  


    return out

'''
Uncomment the following line to generate the MIxS json schema 
from the 'generate_mixs_fields_json' function if the code to generate file has been
uncommented in the 'generate_mixs_fields_json' function
Then, comment the succeeding line, 'MIXS_FIELDS = generate_mixs_fields_json()'
'''
mixs_fields_uri_lst = get_mixs_field_uri()
# print(f'\MIXS fields URI dictionary:\n {json.dumps(mixs_fields_uri_lst, indent=4, sort_keys=False,default=str)}\n')

# MIXS_FIELDS = json.load(open('/copo/common/schema_versions/isa_mappings/mixs_fields.json'))
MIXS_FIELDS = generate_mixs_fields_json()

# print(f'\MIXS_FIELDS:\n {json.dumps(MIXS_FIELDS, indent=4, sort_keys=False,default=str)}\n')

# Create a mapping between the TOL and MIxS fields 
# MIXS_MAPPING = {tol_field: {'field':mixs_field['name'], 'description': mixs_field['name'], 'uri':mixs_field['uri']} for mixs_field in MIXS_FIELDS for tol_field in tol_fields_lst if tol_field.lower() in mixs_field['name']}
def create_tol_mixs_mapping():
    data = dict()
    out = dict()

    for tol_field in tol_fields_lst:
        # Check if the TOL field is in the MIxS field names mapping
        if tol_field in MIXS_FIELD_NAMES_MAPPING:
            mixs_field = MIXS_FIELD_NAMES_MAPPING[tol_field]['mixs']
            mixs_field_uri = mixs_fields_uri_lst.get(mixs_field,str()).get('uri', str())

            mixs_field_info = [mixs_field_dict for mixs_field_dict in MIXS_FIELDS if mixs_field_dict.get('field','') == mixs_field]
        
            for x in mixs_field_info:
                data[tol_field] = {'field':mixs_field, 'type': x['type'], 'regex': x['regex'], 'description': x['description'], 'uri': mixs_field_uri}
                out.update(data)   
          
            continue

        # If the TOL field is not in the MIXS field names mapping,
        mixs_field_info = [mixs_field_dict for mixs_field_dict in MIXS_FIELDS if tol_field.lower().replace('_','') in mixs_field_dict['field'].lower() or tol_field.lower() in mixs_field_dict['field'].lower()]
        
        if mixs_field_info:
            # The length of the 'mixs_field_info' list should be 1, 
            # to signify that there are no duplicates but still 
            # iterate through the list to get the dictionary
            for x in mixs_field_info:
                data[tol_field] = {'field':x['field'], 'type': x['type'], 'regex': x['regex'], 'description': x['description']}
                out.update(data)
            continue         
        else:
            data[tol_field] = {'field':"", 'type': '', 'regex': '', 'description': ""}
            out.update(data)
            continue

    #print(f'\out:\n {json.dumps(out, indent=4, sort_keys=False,default=str)}\n')

    return out

MIXS_MAPPING = create_tol_mixs_mapping()

#print(f'\nMIXS_MAPPING:\n {json.dumps(MIXS_MAPPING, indent=4, sort_keys=False,default=str)}\n')

#___________________________________________________________________

# Helpers for Darwin Core field mappings
dwc_fields_uri_lst ={
    "license": {
        "uri": "http://purl.org/dc/terms/license"
    },
}

DWC_FIELD_NAMES_MAPPING = {
    'COLLECTION_LOCATION': {
        'dwc': 'higherGeography'
    },
    'COLLECTED_BY': {
        'dwc': 'recordedBy'
    },
    'COLLECTOR_AFFILIATION': {
        'dwc': 'institutionCode'
    },
    'COLLECTOR_ORCID_ID': {
        'dwc': 'recordedByID'
    },
    'COLLECTOR_SAMPLE_ID':{
        'dwc': 'materialSampleID'
    },
    'COMMON_NAME': {
        'dwc': 'vernacularName'
    },
    'CULTURE_OR_STRAIN_ID':{
        'dwc':'occurrenceID'
    },
    'DATE_OF_COLLECTION':{
        'dwc':'eventDate'
    },
    'ETHICS_PERMITS_DEF':{
        'dwc': 'license'
    },
    'FAMILY': {
        'dwc': 'family'
    },
    'GAL_SAMPLE_ID:': {
        'dwc': 'institutionID'
    },
    'GENUS': {
        'dwc': 'genus'
    },
    'GRID_REFERENCE': {
        'dwc': 'georeferenceRemarks'
    },
    'IDENTIFIED_BY': {
        'dwc': 'identifiedBy'
    },
    'ORDER_OR_GROUP': {
        'dwc': 'order'
    },
    'ORGANISM_PART': {
        'dwc': 'organismScope'
    },
    'ORIGINAL_COLLECTION_DATE': {
        'dwc': 'eventDate'
    },
    'PRESERVATION_APPROACH': {
        'dwc': 'preparations'
    },
    'SAMPLE_COORDINATOR_AFFILIATION': {
        'dwc': 'institutionCode'
    },
    'SCIENTIFIC_NAME': {
        'dwc': 'scientificName'
    },
    'SERIES': {
        'dwc': 'fieldNumber'
    },
    'SIZE_OF_TISSUE_IN_TUBE':{
        'dwc': 'sampleSizeValue'
    },
    'SPECIMEN_ID': {
        'dwc':'materialSampleID'
    },
    'TIME_OF_COLLECTION': {
        'dwc': 'eventTime'
    },
}

def generate_dwc_fields_json():
    out = list()

    # Get DWC csv schema link from GitHub
    dwc_csv_schema_url =  "https://raw.githubusercontent.com/tdwg/dwc/master/vocabulary/term_versions.csv"
    # Latest dwc term version (2023-09-18): https://rs.tdwg.org/dwc/version/terms/2023-09-18.json

    try:
        # Read the csv schema from the URL
        df = pd.read_csv(dwc_csv_schema_url)

        ''' 
        Get DWC term versions based on the following criteria:
         - latest term versions (based on the 'issued' date column)
         - terms that are not deprecated ('status' != 'deprecated)
         - terms' uri that are from the DWC namespace ('term_iri' starts with 'http://rs.tdwg.org/dwc/terms/')
        
        Then, convert the DWC dataframe to json
        '''
        dwc_uri_prefix = 'http://rs.tdwg.org/dwc/terms/'
        df_latest_term_versions = df.groupby('term_localName')['issued'].transform('max')
        dwc_json_latest_non_deprecated_term_versions = df[(df['issued'] == df_latest_term_versions) & (df['status'] != 'deprecated') & (df['term_iri'].str.startswith(dwc_uri_prefix, na=False))].to_json(orient='records', indent=4)

        # Load the json file to avoid forwarded slashes in the 'term_uri' urls
        dwc_json = json.loads(dwc_json_latest_non_deprecated_term_versions)

        #print(json.dumps(dwc_json, indent=4, sort_keys=False,default=str))
                
        # Rearrange the list of dictionaries and retrieve only the 
        #'term_localName', 'definition', and 'term_iri' keys from the DWC json
        dwc_json = [{'field': d.get('term_localName',''), 'description': d.get('definition',''), 'uri': d.get('term_iri','')}  for d in dwc_json]

        # Append custom items to the dwc_json
        for custom in dwc_fields_uri_lst:
            if custom not in [d.get('field','') for d in dwc_json]:
                field = custom
                uri = dwc_fields_uri_lst[custom]['uri']
                dwc_json.append({'field':field, 'description': '', 'uri': uri})

        # Uncomment the following lines to write the DWC json schema to a file
        # in the '/copo/common/schema_versions/isa_mappings/' directory
        '''
        file_name = "dwc_fields.json"
        file_directory = "/copo/common/schema_versions/isa_mappings/"
        file_path = file_directory + file_name

        with open(file_path, 'w+') as f:
            print(json.dumps(dwc_json, indent=4, sort_keys=False,default=str), file=f)
            f.close()
        '''

        out = dwc_json

    except Exception as e:
        print(f'Error: {e}')
    
    return out

'''
Uncomment the following line to generate the DWC json schema 
from the 'generate_dwc_fields_json' function if the code to generate file has been 
uncommented in the 'generate_dwc_fields_json' function
Then, comment the succeeding line, 'DWC_FIELDS = generate_dwc_fields_json()'
'''
#DWC_FIELDS = json.load(open('/copo/common/schema_versions/isa_mappings/dwc_fields.json'))
DWC_FIELDS = generate_dwc_fields_json()

#print(f'\DWC_FIELDS:\n {json.dumps(DWC_FIELDS, indent=4, sort_keys=False,default=str)}\n')

# Create a mapping between the TOL and DWC fields 
def create_tol_dwc_mapping():
    data = dict()
    out = dict()

    for tol_field in tol_fields_lst:
        # Check if the TOL field is in the DWC field names mapping
        if tol_field in DWC_FIELD_NAMES_MAPPING:
            dwc_field = DWC_FIELD_NAMES_MAPPING[tol_field]['dwc']

            dwc_field_info = [dwc_field_dict for dwc_field_dict in DWC_FIELDS if dwc_field_dict.get('field','') == dwc_field]
        
            for x in dwc_field_info:               
                data[tol_field] = {'field':dwc_field, 'description': x['description'], 'uri': x['uri']}
                out.update(data)   
          
            continue

        # If the TOL field is not in the DWC field names mapping,
        dwc_field_info = [dwc_field_dict for dwc_field_dict in DWC_FIELDS if tol_field.lower().replace('_','') in dwc_field_dict['field'].lower() or tol_field.lower() in dwc_field_dict['field'].lower()]
        
        if dwc_field_info:
            # The length of the 'dwc_field_info' list should be 1, 
            # to signify that there are no duplicates but still 
            # iterate through the list to get the dictionary
            for x in dwc_field_info:
                data[tol_field] = {'field':x['field'], 'description': x['description'], 'uri':x['uri']}
                out.update(data)
            continue        
        else:
            data[tol_field] = {'field':"", 'description': "", 'uri':""}
            out.update(data)
            continue

    #print(f'\out:\n {json.dumps(out, indent=4, sort_keys=False,default=str)}\n')

    return out

DWC_MAPPING = create_tol_dwc_mapping()

#print(f'\nDWC_MAPPING:\n {json.dumps(DWC_MAPPING, indent=4, sort_keys=False,default=str)}\n')

#_______________________________

# Generate 'dwc_ena_mixs_tol_fields_mapping.json' file
output =list()
tol_field_dict = dict()

for tol_field in tol_fields_lst:
    # European Nucleotide Archive (ENA)
    ena = dict()
  
    if tol_field in ENA_FIELD_NAMES_MAPPING:
        ena["field"] = ENA_FIELD_NAMES_MAPPING.get(tol_field, str()).get("ena", str())
        
        ena["type"] = ""
        
        if tol_field in ENA_UNITS_MAPPING:
            ena["unit"] = ENA_UNITS_MAPPING[tol_field]["ena_unit"]
        
        ena["uri"] = ""

        if tol_field in ENA_AND_TOL_RULES and "ena_regex" in list(ENA_AND_TOL_RULES[tol_field].keys()):
            ena["regex"] = ENA_AND_TOL_RULES[tol_field]["ena_regex"]
        
        if tol_field in ENA_AND_TOL_RULES and "human_readable" in list(ENA_AND_TOL_RULES[tol_field].keys()):
            ena["description"] = ENA_AND_TOL_RULES[tol_field]["human_readable"]
        else:
            ena["description"] = ""
    else:
        ena = {"field":"", "uri":"", "description":""}
    #_____________________
    
    # Minimum Information about any (X) Sequence (MIxs)
    # Terms website:  https://genomicsstandardsconsortium.github.io/mixs/term_list/
    mixs = dict()

    if tol_field in list(MIXS_MAPPING.keys()):
        mixs["field"] = MIXS_MAPPING[tol_field]["field"] or str()
        mixs["type"] = MIXS_MAPPING[tol_field]["type"] or str()
        
        if "uri" in list(MIXS_MAPPING[tol_field].keys()):
            mixs["uri"] = MIXS_MAPPING[tol_field]["uri"]
        else:
            mixs["uri"] = ""
        
        if "regex" in list(MIXS_MAPPING[tol_field].keys()):
            mixs["regex"] = MIXS_MAPPING[tol_field]["regex"]

        mixs["description"] = MIXS_MAPPING[tol_field]["description"] or str()
    else:
        mixs = {"field":"","type":"", "uri":"", "regex": "", "description":""}
    
    #_______________________
        
    # Darwin Core (dwc)
    # Terms website: https://dwc.tdwg.org/list/#4-vocabulary
    dwc = dict()

    if tol_field in list(DWC_MAPPING.keys()):
        dwc["field"] = DWC_MAPPING[tol_field]["field"] or str()
      
        if "type" in list(DWC_MAPPING[tol_field].keys()):
            dwc["type"] = DWC_MAPPING[tol_field]["type"]
        
        if "uri" in list(DWC_MAPPING[tol_field].keys()):
            dwc["uri"] = DWC_MAPPING[tol_field]["uri"]
        else:
            dwc["uri"] = ""
        
        if "regex" in list(DWC_MAPPING[tol_field].keys()):
            dwc["regex"] = DWC_MAPPING[tol_field]["regex"]
        
        dwc["description"] = DWC_MAPPING[tol_field]["description"] or str()
    else:
        dwc = {"field":"","type":"", "uri":"", "regex": "", "description":""}

    #_______________________
        
    # Tree of Life (TOL)
    tol = dict()
    tol["field"] = tol_field
    tol["type"] = ""
    tol["uri"] = ""
        
    if tol_field in ENA_AND_TOL_RULES and "strict_regex" in list(ENA_AND_TOL_RULES[tol_field].keys()):
        ena["regex"] = ENA_AND_TOL_RULES[tol_field]["strict_regex"]
        
    if tol_field in ENA_AND_TOL_RULES and "human_readable" in list(ENA_AND_TOL_RULES[tol_field].keys()):
        ena["description"] = ENA_AND_TOL_RULES[tol_field]["human_readable"]
    else:
        ena["description"] = ""  

    # Combine the three dictionaries into one and map it to the TOL field
    tol_field_dict[tol_field] = {"dwc": dwc,"ena": ena,"mixs":mixs,"tol":tol}
    
# Avoid duplication by appending outside the for loop        
output.append(tol_field_dict)

#print(f'\ndwc_ena_mixs_tol_fields_mapping:\n {json.dumps(output, indent=4, sort_keys=False,default=str)}\n')

# Return the list of dictionaries i.e. a .json file in
# the '/copo/common/schema_versions/isa_mappings/' directory
file_name = "dwc_ena_mixs_tol_fields_mapping.json"
file_directory = "/copo/common/schema_versions/isa_mappings/"
file_path = file_directory + file_name

with open(file_path, 'w+') as f:
    print(json.dumps(output, indent=4, sort_keys=False,default=str), file=f)
    f.close()
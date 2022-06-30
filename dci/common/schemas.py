# -*- encoding: utf-8 -*-
#
# Copyright 2018 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from dci.common.exceptions import DCIException
from dci.common.args import parse_args
from jsonschema import validators, FormatChecker, Draft4Validator
from jsonschema.exceptions import ValidationError


def allow_none(property):
    result = property.copy()
    result["type"] = [property["type"], "null"]
    return result


def with_default(property, default):
    result = property.copy()
    result["default"] = default
    if default is None:
        return allow_none(result)
    return result


class Properties(object):
    string = {"type": "string"}
    uuid = {
        "type": "string",
        "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    }
    email = {"type": "string", "format": "email"}
    url = {"type": "string", "format": "uri", "pattern": "^https?://"}
    json = {"type": "object"}
    array = {"type": "array"}
    integer = {"type": "integer"}
    boolean = {"type": "boolean"}
    key_value_csv = {"type": "string", "is_key_value_csv": True}
    positive_integer = {"type": "integer", "minimum": 1}
    positive_or_null_integer = {"type": "integer", "minimum": 0}
    string_integer = {"type": "string", "pattern": "^([+-]?[1-9]\d*|0)$"}
    positive_string_integer = {"type": "string", "pattern": "^[1-9]\d*$"}
    positive_or_null_string_integer = {"type": "string", "pattern": "^\d+$"}
    isoformat_date = {"type": "string", "format": "date-time"}

    @staticmethod
    def enum(accepted_values):
        return {"type": "string", "enum": accepted_values}


def _is_key_value_csv(validator, value, instance, schema):
    for element in instance.split(","):
        if len(tuple(filter(lambda e: e, element.split(":", 1)))) != 2:
            yield ValidationError("'%s' is not a 'key value csv'" % instance)


all_validators = dict(Draft4Validator.VALIDATORS)
all_validators["is_key_value_csv"] = _is_key_value_csv


def extend_with_default(validator_class):
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for property, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(property, subschema["default"])

        for error in validate_properties(validator, properties, instance, schema):
            yield error

    return validators.extend(validator_class, {"properties": set_defaults})


DCIValidator = extend_with_default(
    validators.create(Draft4Validator.META_SCHEMA, validators=all_validators)
)


def _get_error_message(error):
    if error.validator == "pattern":
        custom_error_messages = {
            "uuid": "is not a valid 'uuid'",
            "url": "is not a valid 'url'",
            "string_integer": "is not an integer",
            "positive_string_integer": "is not a positive integer",
            "positive_or_null_string_integer": "is not a positive or null integer",
        }
        property_name = error.relative_path[0]
        value = error.instance
        msg = custom_error_messages.get(property_name, error.message)
        return "%s: '%s' %s" % (property_name, value, msg)

    if (
        error.validator == "type"
        and error.validator_value in ["string", "array", "integer"]
    ) or (error.validator in ["minimum", "is_key_value_csv"]):
        property_name = error.path[-1]
        return "%s: %s" % (property_name, error.message)

    return error.message


def check_json_is_valid(schema, json):
    v = DCIValidator(schema, format_checker=FormatChecker())
    errors = []
    for error in sorted(v.iter_errors(json), key=str):
        errors.append(_get_error_message(error))
    if len(errors):
        raise DCIException("Request malformed", {"errors": errors, "error": errors[0]})


valid_resource_states = ["active", "inactive", "archived"]


def clean_json_with_schema(schema, values):
    check_json_is_valid(schema, values)
    return {k: values[k] for k in schema["properties"].keys() if k in values}


###############################################################################
#                                                                             #
#                                 Args schema                                 #
#                                                                             #
###############################################################################
args_schema = {
    "type": "object",
    "properties": {
        "limit": Properties.positive_string_integer,
        "offset": Properties.positive_or_null_string_integer,
        "sort": Properties.string,
        "where": Properties.key_value_csv,
        "embed": Properties.string,
        "created_after": Properties.isoformat_date,
        "updated_after": Properties.isoformat_date,
    },
    "dependencies": {
        "limit": {"required": ["offset"]},
        "offset": {"required": ["limit"]},
    },
    "additionalProperties": False,
}


def check_and_get_args(raw_args):
    check_json_is_valid(args_schema, raw_args)
    return parse_args(raw_args)


###############################################################################
#                                                                             #
#                                 Job schema                                  #
#                                                                             #
###############################################################################
create_job_properties = {
    "remoteci_id": Properties.uuid,
    "team_id": Properties.uuid,
    "components": Properties.array,
    "comment": with_default(Properties.string, None),
    "previous_job_id": with_default(Properties.uuid, None),
    "update_previous_job_id": with_default(Properties.uuid, None),
    "state": with_default(Properties.enum(valid_resource_states), "active"),
    "topic_id": with_default(Properties.uuid, None),
    "tags": with_default(Properties.array, []),
    "data": with_default(Properties.json, {}),
    "status_reason": with_default(Properties.string, None),
    "configuration": with_default(Properties.string, None),
    "name": with_default(Properties.string, None),
    "url": with_default(Properties.url, None),
}
create_job_schema = {
    "type": "object",
    "properties": create_job_properties,
    "required": ["components"],
    "additionalProperties": False,
}

update_job_properties = {
    "comment": Properties.string,
    "status": Properties.enum(
        [
            "new",
            "pre-run",
            "running",
            "post-run",
            "success",
            "failure",
            "killed",
            "error",
        ]
    ),
    "state": Properties.enum(valid_resource_states),
    "tags": Properties.array,
    "status_reason": Properties.string,
    "configuration": Properties.string,
    "name": Properties.string,
    "url": Properties.url,
}
update_job_schema = {"type": "object", "properties": update_job_properties}


schedule_job_schema = {
    "type": "object",
    "properties": {
        "remoteci_id": Properties.uuid,
        "topic_id": Properties.uuid,
        "components_ids": with_default(Properties.array, []),
        "comment": with_default(Properties.string, None),
        "previous_job_id": with_default(Properties.uuid, None),
        "state": with_default(Properties.enum(valid_resource_states), "active"),
        "tags": with_default(Properties.array, []),
        "data": with_default(Properties.json, {}),
        "configuration": with_default(Properties.string, None),
        "name": with_default(Properties.string, None),
        "url": with_default(Properties.url, None),
    },
    "required": ["topic_id"],
    "additionalProperties": False,
}

upgrade_job_schema = {
    "type": "object",
    "properties": {"job_id": Properties.uuid},
    "required": ["job_id"],
    "additionalProperties": False,
}

add_component_schema = {
    "type": "object",
    "properties": {"id": Properties.uuid},
    "required": ["id"],
    "additionalProperties": False,
}

###############################################################################
#                                                                             #
#                                 Tag schema                                  #
#                                                                             #
###############################################################################
tag_schema = {
    "type": "object",
    "properties": {"name": Properties.string},
    "required": ["name"],
}

###############################################################################
#                                                                             #
#                               Product schema                                #
#                                                                             #
###############################################################################
create_product_properties = {
    "name": Properties.string,
    "label": with_default(Properties.string, None),
    "description": with_default(Properties.string, None),
    "state": with_default(Properties.enum(valid_resource_states), "active"),
}
create_product_schema = {
    "type": "object",
    "properties": create_product_properties,
    "required": ["name"],
    "additionalProperties": False,
}
update_product_properties = {
    "name": Properties.string,
    "label": Properties.string,
    "description": Properties.string,
    "state": Properties.enum(valid_resource_states),
}
update_product_schema = {"type": "object", "properties": update_product_properties}

###############################################################################
#                                                                             #
#                               Product_Team schema                           #
#                                                                             #
###############################################################################
add_team_to_product_schema = {
    "type": "object",
    "properties": {
        "team_id": Properties.uuid,
    },
    "required": ["team_id"],
    "additionalProperties": False,
}

###############################################################################
#                                                                             #
#                                Tests schema                                 #
#                                                                             #
###############################################################################
create_test_properties = {
    "name": Properties.string,
    "team_id": Properties.uuid,
    "state": with_default(Properties.enum(valid_resource_states), "active"),
    "data": with_default(Properties.json, {}),
}
create_test_schema = {
    "type": "object",
    "properties": create_test_properties,
    "required": ["name"],
    "additionalProperties": False,
}

update_test_properties = {
    "name": Properties.string,
    "team_id": Properties.uuid,
    "state": Properties.enum(valid_resource_states),
    "data": Properties.json,
}
update_test_schema = {"type": "object", "properties": update_test_properties}

###############################################################################
#                                                                             #
#                                 User schemas                                #
#                                                                             #
###############################################################################
create_user_properties = {
    "name": Properties.string,
    "fullname": Properties.string,
    "email": Properties.email,
    "timezone": Properties.string,
    "password": Properties.string,
    "state": with_default(Properties.enum(valid_resource_states), "active"),
}
create_user_schema = {
    "type": "object",
    "properties": create_user_properties,
    "required": ["name", "fullname", "email"],
    "additionalProperties": False,
}

update_user_properties = {
    "name": Properties.string,
    "fullname": Properties.string,
    "email": Properties.email,
    "timezone": Properties.string,
    "password": Properties.string,
    "team_id": Properties.uuid,
    "state": Properties.enum(valid_resource_states),
}
update_user_schema = {"type": "object", "properties": update_user_properties}

###############################################################################
#                                                                             #
#                            Current User/Identity schema                     #
#                                                                             #
###############################################################################
update_current_user_schema = {
    "type": "object",
    "properties": {
        "current_password": Properties.string,
        "new_password": Properties.string,
        "fullname": Properties.string,
        "email": Properties.email,
        "timezone": Properties.string,
    },
}

###############################################################################
#                                                                             #
#                                Feeder schema                                #
#                                                                             #
###############################################################################
create_feeder_properties = {
    "name": Properties.string,
    "team_id": Properties.uuid,
    "state": with_default(Properties.enum(valid_resource_states), "active"),
    "data": with_default(Properties.json, {}),
}
create_feeder_schema = {
    "type": "object",
    "properties": create_feeder_properties,
    "required": ["name", "team_id"],
    "additionalProperties": False,
}

update_feeder_properties = {
    "name": Properties.string,
    "team_id": Properties.uuid,
    "state": Properties.enum(valid_resource_states),
    "data": Properties.json,
}
update_feeder_schema = {"type": "object", "properties": update_feeder_properties}


###############################################################################
#                                                                             #
#                              Remote CI schema                                #
#                                                                             #
###############################################################################
create_remoteci_properties = {
    "name": Properties.string,
    "team_id": Properties.uuid,
    "state": with_default(Properties.enum(valid_resource_states), "active"),
    "data": with_default(Properties.json, {}),
    "public": with_default(Properties.boolean, False),
}
create_remoteci_schema = {
    "type": "object",
    "properties": create_remoteci_properties,
    "required": ["name", "team_id"],
    "additionalProperties": False,
}

update_remoteci_properties = {
    "name": Properties.string,
    "team_id": Properties.uuid,
    "state": Properties.enum(valid_resource_states),
    "data": Properties.json,
    "public": Properties.boolean,
}
update_remoteci_schema = {"type": "object", "properties": update_remoteci_properties}


###############################################################################
#                                                                             #
#                                 Component schema                            #
#                                                                             #
###############################################################################
create_component_properties = {
    "name": Properties.string,
    "title": with_default(Properties.string, None),
    "message": with_default(Properties.string, None),
    "canonical_project_name": with_default(Properties.string, None),
    "url": with_default(Properties.url, None),
    "type": Properties.string,
    "topic_id": Properties.uuid,
    "team_id": Properties.uuid,
    "state": with_default(Properties.enum(valid_resource_states), "active"),
    "data": with_default(Properties.json, {}),
    "tags": with_default(Properties.array, []),
    "released_at": Properties.isoformat_date,
}
create_component_schema = {
    "type": "object",
    "properties": create_component_properties,
    "required": ["name", "type", "topic_id"],
    "additionalProperties": False,
}

update_component_properties = {
    "name": Properties.string,
    "title": Properties.string,
    "message": Properties.string,
    "canonical_project_name": Properties.string,
    "export_control": Properties.boolean,
    "url": Properties.url,
    "type": Properties.string,
    "topic_id": Properties.uuid,
    "state": Properties.enum(valid_resource_states),
    "data": Properties.json,
    "tags": Properties.array,
}
update_component_schema = {"type": "object", "properties": update_component_properties}

###############################################################################
#                                                                             #
#                          Counter schemas                                    #
#                                                                             #
###############################################################################
counter_properties = {"sequence": Properties.integer}
counter_schema = {
    "type": "object",
    "properties": counter_properties,
    "required": ["sequence"],
    "additionalProperties": False,
}

###############################################################################
#                                                                             #
#                             Job State schemas                               #
#                                                                             #
###############################################################################
jobstate_properties = {
    "status": Properties.string,
    "job_id": Properties.uuid,
    "comment": with_default(Properties.string, None),
}
jobstate_schema = {
    "type": "object",
    "properties": jobstate_properties,
    "required": ["status", "job_id"],
    "additionalProperties": False,
}

###############################################################################
#                                                                             #
#                                 Topic schema                                #
#                                                                             #
###############################################################################
create_topic_properties = {
    "name": Properties.string,
    "data": with_default(Properties.json, {}),
    "product_id": Properties.uuid,
    "next_topic_id": with_default(Properties.uuid, None),
    "state": with_default(Properties.enum(valid_resource_states), "active"),
    "component_types": with_default(Properties.array, []),
    "component_types_optional": with_default(Properties.array, []),
    "export_control": with_default(Properties.boolean, False),
}
create_topic_schema = {
    "type": "object",
    "properties": create_topic_properties,
    "required": ["name", "product_id"],
    "additionalProperties": False,
}

update_topic_properties = {
    "name": Properties.string,
    "data": Properties.json,
    "product_id": Properties.uuid,
    "next_topic_id": allow_none(Properties.uuid),
    "state": Properties.enum(valid_resource_states),
    "component_types": Properties.array,
    "component_types_optional": Properties.array,
    "export_control": Properties.boolean,
}
update_topic_schema = {"type": "object", "properties": update_topic_properties}


###############################################################################
#                                                                             #
#                               Topic_Team schema                             #
#                                                                             #
###############################################################################
add_team_to_topic_schema = {
    "type": "object",
    "properties": {
        "team_id": Properties.uuid,
    },
    "required": ["team_id"],
    "additionalProperties": False,
}

###############################################################################
#                                                                             #
#                                  Team schema                                #
#                                                                             #
###############################################################################
create_team_properties = {
    "name": Properties.string,
    "country": with_default(Properties.string, None),
    "state": with_default(Properties.enum(valid_resource_states), "active"),
    "external": with_default(Properties.boolean, False),
}
create_team_schema = {
    "type": "object",
    "properties": create_team_properties,
    "required": ["name"],
    "additionalProperties": False,
}

update_team_properties = {
    "name": Properties.string,
    "country": allow_none(Properties.string),
    "state": Properties.enum(valid_resource_states),
    "external": Properties.boolean,
}
update_team_schema = {"type": "object", "properties": update_team_properties}

###############################################################################
#                                                                             #
#                                  File schema                                #
#                                                                             #
###############################################################################
file_upload_certification_properties = {
    "username": Properties.string,
    "password": Properties.string,
    "certification_id": Properties.string,
}
file_upload_certification_schema = {
    "type": "object",
    "properties": file_upload_certification_properties,
    "required": ["username", "password", "certification_id"],
    "additionalProperties": False,
}


###############################################################################
#                                                                             #
#                                  Analytics schema                           #
#                                                                             #
###############################################################################

analytics_task_duration_cumulated_properties = {
    "topic_id": Properties.uuid,
    "remoteci_id": Properties.uuid,
}
analytics_task_duration_cumulated = {
    "type": "object",
    "properties": analytics_task_duration_cumulated_properties,
    "required": ["topic_id", "remoteci_id"],
    "additionalProperties": False,
}


analytics_task_components_coverage_properties = {
    "topic_id": Properties.uuid,
    "team_id": with_default(Properties.string, None),
    "types": with_default(Properties.string, None),
}
analytics_task_components_coverage = {
    "type": "object",
    "properties": analytics_task_components_coverage_properties,
    "required": ["topic_id"],
    "additionalProperties": False,
}

analytics_tasks_junit_properties = {
    "topic_1_id": Properties.string,
    "topic_1_start_date": Properties.string,
    "topic_1_end_date": Properties.string,
    "remoteci_1_id": Properties.string,
    "topic_1_baseline_computation": Properties.string,
    "tags_1": with_default(Properties.array, []),
    "topic_2_id": Properties.string,
    "topic_2_start_date": Properties.string,
    "topic_2_end_date": Properties.string,
    "remoteci_2_id": Properties.string,
    "topic_2_baseline_computation": Properties.string,
    "tags_2": with_default(Properties.array, []),
    "test_name": Properties.string,
}
analytics_tasks_junit = {
    "type": "object",
    "properties": analytics_tasks_junit_properties,
    "required": [
        "topic_1_id",
        "topic_1_start_date",
        "topic_1_end_date",
        "remoteci_1_id",
        "topic_1_baseline_computation",
        "tags_1",
        "topic_2_id",
        "topic_2_start_date",
        "topic_2_end_date",
        "remoteci_2_id",
        "topic_2_baseline_computation",
        "tags_2",
        "test_name",
    ],
    "additionalProperties": False,
}

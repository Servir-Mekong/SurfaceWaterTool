# -*- coding: utf-8 -*-

# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: google/api/source_info.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
    name="google/api/source_info.proto",
    package="google.api",
    syntax="proto3",
    serialized_options=b"\n\016com.google.apiB\017SourceInfoProtoP\001ZEgoogle.golang.org/genproto/googleapis/api/serviceconfig;serviceconfig\242\002\004GAPI",
    serialized_pb=b'\n\x1cgoogle/api/source_info.proto\x12\ngoogle.api\x1a\x19google/protobuf/any.proto"8\n\nSourceInfo\x12*\n\x0csource_files\x18\x01 \x03(\x0b\x32\x14.google.protobuf.AnyBq\n\x0e\x63om.google.apiB\x0fSourceInfoProtoP\x01ZEgoogle.golang.org/genproto/googleapis/api/serviceconfig;serviceconfig\xa2\x02\x04GAPIb\x06proto3',
    dependencies=[google_dot_protobuf_dot_any__pb2.DESCRIPTOR],
)


_SOURCEINFO = _descriptor.Descriptor(
    name="SourceInfo",
    full_name="google.api.SourceInfo",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="source_files",
            full_name="google.api.SourceInfo.source_files",
            index=0,
            number=1,
            type=11,
            cpp_type=10,
            label=3,
            has_default_value=False,
            default_value=[],
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR,
        )
    ],
    extensions=[],
    nested_types=[],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax="proto3",
    extension_ranges=[],
    oneofs=[],
    serialized_start=71,
    serialized_end=127,
)

_SOURCEINFO.fields_by_name[
    "source_files"
].message_type = google_dot_protobuf_dot_any__pb2._ANY
DESCRIPTOR.message_types_by_name["SourceInfo"] = _SOURCEINFO
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

SourceInfo = _reflection.GeneratedProtocolMessageType(
    "SourceInfo",
    (_message.Message,),
    {
        "DESCRIPTOR": _SOURCEINFO,
        "__module__": "google.api.source_info_pb2"
        # @@protoc_insertion_point(class_scope:google.api.SourceInfo)
    },
)
_sym_db.RegisterMessage(SourceInfo)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)

"""Minimal protobuf wire-format reader for v2fly's compiled ``dlc.dat``.

``dlc.dat`` is a ``GeoSiteList``:

    message Domain { Type type = 1; string value = 2; repeated Attribute attribute = 3; }
    message Attribute { string key = 1; bool bool_value = 2; }
    message GeoSite { string country_code = 1; repeated Domain domain = 2; }
    message GeoSiteList { repeated GeoSite entry = 1; }

We only need five lines of schema, so a full protobuf dependency is not
justified; this reader decodes exactly the wire types those messages use and
errors loudly on anything else.
"""

from __future__ import annotations

from dataclasses import dataclass

WIRE_VARINT = 0
WIRE_64BIT = 1
WIRE_LENGTH = 2
WIRE_32BIT = 5


class ProtobufError(ValueError):
    pass


def read_varint(data: bytes, offset: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while True:
        if offset >= len(data):
            raise ProtobufError("truncated varint")
        byte = data[offset]
        offset += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, offset
        shift += 7
        if shift > 63:
            raise ProtobufError("varint too long")


def iter_fields(data: bytes):
    """Yield ``(field_number, wire_type, value)``; value is bytes or int."""
    offset = 0
    while offset < len(data):
        key, offset = read_varint(data, offset)
        field_number, wire_type = key >> 3, key & 0x07
        if wire_type == WIRE_VARINT:
            value, offset = read_varint(data, offset)
        elif wire_type == WIRE_LENGTH:
            length, offset = read_varint(data, offset)
            if offset + length > len(data):
                raise ProtobufError("truncated length-delimited field")
            value, offset = data[offset : offset + length], offset + length
        elif wire_type == WIRE_64BIT:
            value, offset = data[offset : offset + 8], offset + 8
        elif wire_type == WIRE_32BIT:
            value, offset = data[offset : offset + 4], offset + 4
        else:
            raise ProtobufError(f"unsupported wire type {wire_type}")
        yield field_number, wire_type, value


@dataclass(frozen=True)
class DatDomain:
    type: int
    value: str
    attributes: tuple[str, ...]


def _parse_domain(data: bytes) -> DatDomain:
    domain_type = 0
    value = b""
    attributes: list[str] = []
    for field, wire, raw in iter_fields(data):
        if field == 1 and wire == WIRE_VARINT:
            domain_type = int(raw)
        elif field == 2 and wire == WIRE_LENGTH:
            value = raw
        elif field == 3 and wire == WIRE_LENGTH:
            key = b""
            for sub_field, sub_wire, sub_raw in iter_fields(raw):
                if sub_field == 1 and sub_wire == WIRE_LENGTH:
                    key = sub_raw
            if key:
                attributes.append(key.decode("utf-8", "replace"))
    return DatDomain(domain_type, value.decode("utf-8", "replace"), tuple(attributes))


def parse_geosite_list(data: bytes) -> dict[str, list[DatDomain]]:
    """Decode ``dlc.dat`` into ``{category: [domain, ...]}``."""
    if not data:
        raise ProtobufError("empty dlc.dat")
    result: dict[str, list[DatDomain]] = {}
    for field, wire, raw in iter_fields(data):
        if field != 1 or wire != WIRE_LENGTH:
            continue
        name = ""
        domains: list[DatDomain] = []
        for sub_field, sub_wire, sub_raw in iter_fields(raw):
            if sub_field == 1 and sub_wire == WIRE_LENGTH:
                name = sub_raw.decode("utf-8", "replace")
            elif sub_field == 2 and sub_wire == WIRE_LENGTH:
                domains.append(_parse_domain(sub_raw))
        if name:
            # v2fly stores list names upper-cased; keep the lookup API lower-case.
            result[name.lower()] = domains
    if not result:
        raise ProtobufError("dlc.dat contains no categories; format changed?")
    return result

#!/usr/bin/env python
"""Tests for the ee.serializer module."""



import json
import six

import unittest

import ee
from ee import apitestcase
from ee import serializer


def _max_depth(x):
  """Computes the maximum nesting level of some dict/list."""
  if isinstance(x, dict):
    return 1 + max(_max_depth(v) for v in six.itervalues(x))
  elif isinstance(x, list):
    return 1 + max(_max_depth(v) for v in x)
  else:
    return 1


class SerializerTest(apitestcase.ApiTestCase):

  def testSerialization(self):
    """Verifies a complex serialization case."""

    class ByteString(ee.Encodable):
      """A custom Encodable class that does not use invocations.

      This one is actually supported by the EE API encoding.
      """

      def __init__(self, value):
        """Creates a bytestring with a given string value."""
        self._value = value

      def encode(self, unused_encoder):  # pylint: disable-msg=g-bad-name
        return {'type': 'Bytes', 'value': self._value}

      def encode_cloud_value(self, unused_encoder):
        # Proto3 JSON embedding of "bytes" values uses base64 encoding, which
        # this already is.
        return {'bytesValue': self._value}

    call = ee.ComputedObject('String.cat', {'string1': 'x', 'string2': 'y'})
    body = lambda x, y: ee.CustomFunction.variable(None, 'y')
    sig = {'returns': 'Object',
           'args': [
               {'name': 'x', 'type': 'Object'},
               {'name': 'y', 'type': 'Object'}]}
    custom_function = ee.CustomFunction(sig, body)
    to_encode = [
        None,
        True,
        5,
        7,
        3.4,
        112233445566778899,
        'hello',
        ee.Date(1234567890000),
        ee.Geometry(ee.Geometry.LineString(1, 2, 3, 4), 'SR-ORG:6974'),
        ee.Geometry.Polygon([
            [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]],
            [[5, 6], [7, 6], [7, 8], [5, 8]],
            [[1, 1], [2, 1], [2, 2], [1, 2]]
        ]),
        ByteString('aGVsbG8='),
        {
            'foo': 'bar',
            'baz': call
        },
        call,
        custom_function
    ]

    self.assertEqual(
        apitestcase.ENCODED_JSON_SAMPLE,
        json.loads(serializer.toJSON(to_encode, for_cloud_api=False)))
    encoded = serializer.encode(to_encode, for_cloud_api=True)
    self.assertEqual(apitestcase.ENCODED_CLOUD_API_JSON_SAMPLE, encoded)
    pretty_encoded = serializer.encode(
        to_encode, is_compound=False, for_cloud_api=True)
    self.assertEqual(apitestcase.ENCODED_CLOUD_API_JSON_SAMPLE_PRETTY,
                     pretty_encoded)

    encoded_json = serializer.toJSON(to_encode, for_cloud_api=True)
    decoded_encoded_json = json.loads(encoded_json)
    self.assertEqual(encoded, decoded_encoded_json)

  def testRepeats(self):
    """Verifies serialization finds and removes repeated values."""
    test1 = ee.Image(5).mask(ee.Image(5))     # pylint: disable-msg=no-member
    expected1 = {
        'type': 'CompoundValue',
        'scope': [
            ['0', {
                'type': 'Invocation',
                'arguments': {
                    'value': 5
                },
                'functionName': 'Image.constant'
            }],
            ['1', {
                'type': 'Invocation',
                'arguments': {
                    'image': {
                        'type': 'ValueRef',
                        'value': '0'
                    },
                    'mask': {
                        'type': 'ValueRef',
                        'value': '0'
                    }
                },
                'functionName': 'Image.mask'
            }]
        ],
        'value': {
            'type': 'ValueRef',
            'value': '1'
        }
    }
    self.assertEqual(expected1,
                     json.loads(serializer.toJSON(test1, for_cloud_api=False)))
    expected_cloud = {
        'values': {
            '0': {
                'functionInvocationValue': {
                    'arguments': {
                        'image': {
                            'valueReference': '1'
                        },
                        'mask': {
                            'valueReference': '1'
                        }
                    },
                    'functionName': 'Image.mask'
                }
            },
            '1': {
                'functionInvocationValue': {
                    'arguments': {
                        'value': {
                            'constantValue': 5
                        }
                    },
                    'functionName': 'Image.constant'
                }
            }
        },
        'result': '0'
    }
    expected_cloud_pretty = {
        'functionInvocationValue': {
            'arguments': {
                'image': {
                    'functionInvocationValue': {
                        'arguments': {
                            'value': {
                                'constantValue': 5
                            }
                        },
                        'functionName': 'Image.constant'
                    }
                },
                'mask': {
                    'functionInvocationValue': {
                        'arguments': {
                            'value': {
                                'constantValue': 5
                            }
                        },
                        'functionName': 'Image.constant'
                    }
                }
            },
            'functionName': 'Image.mask'
        }
    }
    self.assertEqual(expected_cloud, serializer.encode(
        test1, for_cloud_api=True))
    self.assertEqual(
        expected_cloud_pretty,
        serializer.encode(test1, is_compound=False, for_cloud_api=True))

  def testDepthLimit_withAlgorithms(self):
    x = ee.Number(0)
    for i in range(100):
      x = x.add(ee.Number(i))
    encoded = serializer.encode(x, for_cloud_api=True)
    # The default depth limit is 50, but there's some slop, so be a little loose
    # on the test.
    self.assertLess(_max_depth(encoded), 60)

  def testDepthLimit_withLists(self):
    x = ee.List([0])
    for i in range(100):
      x = ee.List([i, x])
    encoded = serializer.encode(x, for_cloud_api=True)
    self.assertLess(_max_depth(encoded), 60)

  def testDepthLimit_withDictionaries(self):
    x = ee.Dictionary({0: 0})
    for i in range(100):
      x = ee.Dictionary({i: x})
    encoded = serializer.encode(x, for_cloud_api=True)
    self.assertLess(_max_depth(encoded), 60)


if __name__ == '__main__':
  unittest.main()

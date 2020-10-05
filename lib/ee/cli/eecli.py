#!/usr/bin/env python
"""Executable for the Earth Engine command line interface.

This executable starts a Python Cmd instance to receive and process command
line input entered by the user. If the executable is invoked with some
command line arguments, the Cmd is launched in the one-off mode, where
the provided arguments are processed as a single command after which the
program is terminated. Otherwise, this executable will launch the Cmd in the
interactive (looping) mode, where the user will be able to run multiple
commands as in a typical terminal program.
"""

from __future__ import print_function

import argparse
import sys

import ee
from ee.cli import commands
from ee.cli import utils


class CommandDispatcher(commands.Dispatcher):
  name = 'main'
  COMMANDS = commands.EXTERNAL_COMMANDS


def _run_command(*argv):
  """Runs an eecli command."""
  _ = argv

  # Set the program name to 'earthengine' for proper help text display.
  parser = argparse.ArgumentParser(
      prog='earthengine', description='Earth Engine Command Line Interface.')
  parser.add_argument(
      '--ee_config', help='Path to the earthengine configuration file. '
      'Defaults to "~/%s".' % utils.DEFAULT_EE_CONFIG_FILE_RELATIVE)
  parser.add_argument(
      '--service_account_file', help='Path to a service account credentials'
      'file.  Overrides any ee_config if specified.')
  parser.add_argument(
      '--use_cloud_api',
      help='Enables the new experimental EE Cloud API backend. (on by default)',
      action='store_true',
      dest='use_cloud_api')
  parser.add_argument(
      '--no-use_cloud_api',
      help='Disables the new experimental EE Cloud API backend.',
      action='store_false',
      dest='use_cloud_api')
  parser.add_argument(
      '--project',
      help='Specifies a Google Cloud Platform Project id to override the call.',
      dest='project_override')
  parser.set_defaults(use_cloud_api=True)

  dispatcher = CommandDispatcher(parser)

  # Print the list of commands if the user supplied no arguments at all.
  if len(sys.argv) == 1:
    parser.print_help()
    return

  args = parser.parse_args()
  config = utils.CommandLineConfig(
      args.ee_config, args.service_account_file, args.use_cloud_api,
      args.project_override
  )

  # TODO(user): Remove this warning once things are officially launched
  #  and the old API is removed.
  if args.use_cloud_api:
    print('Running command using Cloud API.  Set --no-use_cloud_api to '
          'go back to using the API\n')

  # Catch EEException errors, which wrap server-side Earth Engine
  # errors, and print the error message without the irrelevant local
  # stack trace. (Individual commands may also catch EEException if
  # they want to be able to continue despite errors.)
  try:
    dispatcher.run(args, config)
  except ee.EEException as e:
    print(e)
    sys.exit(1)


def _get_tensorflow():
  try:
    # pylint: disable=g-import-not-at-top
    import tensorflow.compat.v1 as tf
    return tf
  except ImportError:
    return None


def main():
  tf_module = _get_tensorflow()
  if tf_module:
    # We need InitGoogle initialization since TensorFlow expects it.
    tf_module.app.run(_run_command, argv=sys.argv[:1])
  else:
    _run_command()


if __name__ == '__main__':
  main()

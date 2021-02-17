import argparse
import configparser
import json
import logging.config
import time
import urllib.parse
import urllib.request
import yaml

######################################################################################################
# Parse command line.
######################################################################################################

args_parser = argparse.ArgumentParser()
args_parser.add_argument('--flat', dest='flat', required=False, default=True, action='store_true', help='specify if configuration keys are dot-separated strings')
args_parser.add_argument('--no-flat', dest='flat', required=False, default=True, action='store_false', help='specify if configuration keys are heirarchical and separated by a forward slash (/)')
args_parser.add_argument('--parent', required=True, help='containing folder or key in Consul under which new KV pairs are located')
args_parser.add_argument('--upload', required=True, help='specifies configuration file to upload to KV data store in Consul')
args = args_parser.parse_args()

######################################################################################################
# Read program configuration.
######################################################################################################

config = configparser.ConfigParser()
config.read(f'config/cf2kv.ini')
defaults = config['DEFAULT']

######################################################################################################
# Set up logging.
######################################################################################################

logging_config_file = 'config/logging.yml'
with open(logging_config_file, 'r') as lcf:
    logging.config.dictConfig(yaml.safe_load(lcf.read()))
    logger = logging.getLogger("cf2ky-logger")

######################################################################################################
# Rock.
######################################################################################################

def read_configuration_file(fname:str):
    # Assume *.properties contain Java properties.
    if fname.endswith('.properties'):
        try:
            with open(fname, 'r') as java_properties:
                properties = java_properties.read().splitlines()
        except:
            logger.error(f'Could not open Java properties file {fname}.', exc_info=True)
            return None
        kv_pairs = []
        for p in properties:
            kv = p.split('=')
            kv_pairs.append({kv[0]: kv[1]})
        return kv_pairs

    # Assume *.yml and *.yaml are YAML configurations, and *.json contain JSON objects.
    if fname.endswith('.yml') or fname.endswith('.yaml') or fname.endswith('.json'):
        if fname.endswith('.yml') or fname.endswith('.yaml'):
            try:
                with open(fname, 'r') as yaml_cf:
                    ydict = yaml.safe_load(yaml_cf.read())
            except:
                logger.error(f'Could not open YAML file {fname}.', exc_info=True)
                return None
        else:
            try:
                with open(fname, 'r') as json_cf:
                    ydict = json.load(json_cf)
            except:
                logger.error(f'Could not open JSON file {fname}.', exc_info=True)
                return None

        if type(ydict) != dict: return None # Only support dictionary trees.

        kv_pairs = []
        prefix_stack = [['', ydict]] # each element is a (prefix, dictionary) tuple.
        while len(prefix_stack) > 0:
            cur_prefix, cur_dict = prefix_stack.pop()
            for key in cur_dict:
                nxt_prefix = f'{cur_prefix}.{key}' if len(cur_prefix) > 0 else key
                val = cur_dict[key]
                if type(val) == dict:
                    prefix_stack.append([nxt_prefix, val])
                else:
                    kv_pairs.append({nxt_prefix: val})
        return kv_pairs

    return None

def upload_configuration_to_consul():
    # Read in configuration file.
    kv_pairs = read_configuration_file(args.upload)
    if not kv_pairs:
        logger.error(f'Could not read in configuration file {args.upload} to upload to KV data store in Consul.')
        return

    logger.debug(f'kv_pairs={kv_pairs}')
    api_base_url = defaults.get('consul.url')
    query_params = urllib.parse.urlencode({'flags': int(time.time())})

    logger.debug(f'Uploading KV pairs for file={args.upload}, parent={args.parent}, flat={args.flat}')
    for kv in kv_pairs:
        logger.debug(f'kv={kv}')
        key, value = next((str(k), str(v)) for k, v in kv.items())
        if not args.flat: key = key.replace('.', '/')
        req = urllib.request.Request(
            url = f'{api_base_url}/{args.parent}/{key}?{query_params}',
            headers = {
                'Accept': 'application/json'
            },
            data = value.encode('utf-8'),
            method = 'PUT'
        )
        upload_result = False
        try:
            with urllib.request.urlopen(req) as upload_fh:
                upload_result = json.loads(upload_fh.read().decode('utf-8'))
        except:
            logger.error(f'Could not upload KV pair for key={key} to URL {req.full_url}', exc_info=True)
        if upload_result:
            logger.info(f'Successfully uploaded KV pair with key={key}')
        else:
            logger.error(f'Failed to upload KV pair with key={key} to URL {req.full_url}')

if __name__ == "__main__":
    upload_configuration_to_consul()

# cf2kv

This is a Python program that imports offline configuration files into a [key-value data store housed in Consul](https://www.consul.io/docs/dynamic-app-config/kv).  Configuration file-formats supported are:

* Regular Java-style `*.properties` files.
* JSON files (ie, files that house a javascript object).
* YAML files.

We do a fairly naive import in that we do not discriminate between environments (Eg, development versus production), we don't optimize on network consumption, and we hit KV API endpoints irrespective of corporate ACL conventions and/or session-based locks.  Please feel free to make improvements, as needs be.

We release this package under the MIT License.

## Examples of command-line operation

Before trying out any of the examples, be sure to make certain your operating environment meets sufficient requirements.  You should have Python 3.x installed.  Then make sure you have the right dependencies by running something like this:

    $ pip3 install -r requirements.txt

Look over `config/cf2kv.ini` to be sure the property `consul.url` is pointing at the right instance of the KV data store in consul.

### Import Java-style properties file into Consul.

Run the program like this:

    $ python3 cf2ky.py --upload examples/example.properties --parent test123 --no-flat

In this case, a property like

    its.a.wonderful.life=true

will be mirrored back to consul as a property with key `its/a/wonderful/life` and a value of `true`.

Enjoy!
# hacs_zabbix_problems
Homeassistant HACS integration to import Zabbix problems as entities

Use HACS to import this repository and install the zabbix_problems integration into Homeassistant.

In Homeassistant -> Settings -> Devices -> Add Integration choose zabbix_problems.

Configure your Zabbix credentials in the first menu. After that add as many sensors as you like. 
The sensor name will be sensor.zbx_<your_input> and it will watch for problems matching the tags 
you specified in the setup menu. If you want to watch for multiple tags seperate them with a comma.
The zabbix tags and associated values have to be specified in the form tag:value.

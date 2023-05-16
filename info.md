Homeassistant custom integration installable via HACS

This integration imports problems from Zabbix as homeassistant sensors. Each
sensor is associated with a list of Zabbix probleam tags to watch for. The 
stae of the sensor is set to the value of the problem with the highest severity.

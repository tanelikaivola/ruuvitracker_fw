import pyb
from .powerdomains import powerdomains_base

# MicroSD, GPS Antenna
LDO2        = powerdomains_base(pyb.Pin('ENABLE_LDO2', pyb.Pin.OUT_PP))
# GPS_VCC
LDO3        = powerdomains_base(pyb.Pin('ENABLE_LDO3', pyb.Pin.OUT_PP))
# Expansion port
LDO4        = powerdomains_base(pyb.Pin('ENABLE_LDO4', pyb.Pin.OUT_PP))
GSM_VBAT    = powerdomains_base(pyb.Pin('ENABLE_GSM_VBAT', pyb.Pin.OUT_PP))
# GPS backup power, for warm starts...
GPS_VBACKUP = powerdomains_base(pyb.Pin('GPS_V_BACKUP_PWR', pyb.Pin.OUT_PP))

# List of unique domains
domains_list = [ LDO2, LDO3, LDO4, GSM_VBAT, GPS_VBACKUP ]

# Aliases for domains
GPS_VCC = LDO3
GPS_ANT = LDO2
SDCARD = LDO2



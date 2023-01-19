# Aardvark_probe
A simple wrapper for Aardvark USB I²C/SPI adapter, develop with python3.

# Features
- configuration through toml config file
- SPI master support
- GPIO support

# Dependencies
- Total Phase Aardvark Python API: aardvark_py
   -> https://aardvark-py.readthedocs.io/en/master/

# Config file Exemple
```toml
[Probe]
SerialId = xxxx
EnablePin = "SPI_ONLY"

[SPI]
Bitrate = 2000
Mode = 0
Bitorder = 0
SsPolarity = 0

[Direction]
AA_GPIO_SCL_Pin_1	= 1	
AA_GPIO_SDA_Pin_3	= 0	
AA_GPIO_MISO_Pin_5	= 0	
AA_GPIO_SCK_Pin_7	= 0	
AA_GPIO_MOSI_Pin_8	= 0	
AA_GPIO_SS_Pin_9	= 0

[PullUp]
AA_GPIO_SCL_Pin_1	= 0	
AA_GPIO_SDA_Pin_3	= 0	
AA_GPIO_MISO_Pin_5	= 0	
AA_GPIO_SCK_Pin_7	= 0	
AA_GPIO_MOSI_Pin_8	= 0	
AA_GPIO_SS_Pin_9	= 0	 
```
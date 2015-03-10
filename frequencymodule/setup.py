from distutils.core import setup, Extension


setup(name='frequency_module', version='1.0',  \
      ext_modules=[Extension('frequency_module', ['frequencymodule.c', 'event_gpio.c', 'common.c'])])
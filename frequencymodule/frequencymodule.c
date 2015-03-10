// frequencymodule.c
// Author: Brandon Mayfield

#include <Python.h>
#include "common.h"
#include "event_gpio.h"
#include "time.h"


#define RISING_EDGE  1

static PyObject* read_frequency_calc(PyObject* self, PyObject *args)
{
    clock_t start, finish;
    double duration;
    unsigned int gpio;
    int cycles, result;
    char *channel;
    char error[30];
    int x = 0; 

    if (!PyArg_ParseTuple(args, "si", &channel, &cycles))
        return NULL;

    if (get_gpio_number(channel, &gpio)) {
        PyErr_SetString(PyExc_RuntimeError, "Invalid Pin");
        return NULL;
    }

    if (cycles < 0) {
        PyErr_SetString(PyExc_RuntimeError, "Cycles must be greater than 0");
        return NULL;
   }
    

    Py_BEGIN_ALLOW_THREADS // disable GIL
    
    start=clock();
    while (x < cycles) {
        result = blocking_wait_for_edge(gpio, RISING_EDGE);
        x++;   
    }
    sleep(1);
    finish=clock();
    
    Py_END_ALLOW_THREADS   // enable GIL

    duration=(float)(finish -start)/CLOCKS_PER_SEC;
    
    if (result == 0) {
        return Py_BuildValue("f", duration);
    } else if (result == 2) {
        PyErr_SetString(PyExc_RuntimeError, "Edge detection events already enabled for this GPIO channel");
        return NULL;
    } else {
        sprintf(error, "Error #%d waiting for edge", result);
        PyErr_SetString(PyExc_RuntimeError, error);
        return NULL;
    }
   
    return Py_BuildValue("f", start);
}

static PyMethodDef read_frequency_funcs[] = {
    {"read_frequency", (PyCFunction)read_frequency_calc, 
     METH_VARARGS, "Usage: read_frequency(pin, cycles)\n"},
    {NULL}
};

PyMODINIT_FUNC initfrequency_module(void)
{
    Py_InitModule("frequency_module", read_frequency_funcs);
}
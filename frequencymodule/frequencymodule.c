// frequencymodule.c
// Author: Brandon Mayfield

#include <Python.h>
#include "common.h"
#include "event_gpio.h"
#include "time.h"
#include <sched.h>


#define RISING_EDGE  1

static PyObject* read_frequency_calc(PyObject* self, PyObject *args)
{
    clock_t start, finish;
    float duration, frequency;
    unsigned int gpio;
    int cycles, result;
    char *channel;
    char error[30];
    int x = 0;
    
    struct sched_param sched;
    memset(&sched, 0, sizeof(sched));
    // Use FIFO scheduler with highest priority for the lowest chance of the kernel context switching.
    sched.sched_priority = sched_get_priority_max(SCHED_FIFO);
    sched_setscheduler(0, SCHED_FIFO, &sched);

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
        x = x + 1;   
    }
    sleep(1);
    finish=clock();
    
    Py_END_ALLOW_THREADS   // enable GIL

    duration=(float)(finish - start)/CLOCKS_PER_SEC;
    
    duration = (duration-1) * 2;
    
    frequency = (float)(cycles/duration);
    
    if (result == 0) {
        return Py_BuildValue("d", frequency);
    } else if (result == 2) {
        PyErr_SetString(PyExc_RuntimeError, "Edge detection events already enabled for this GPIO channel");
        return NULL;
    } else {
        sprintf(error, "Error #%d waiting for edge", result);
        PyErr_SetString(PyExc_RuntimeError, error);
        return NULL;
    }
   
    return Py_BuildValue("s", 'what?');
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
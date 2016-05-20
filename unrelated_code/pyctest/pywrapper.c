#include <Python.h>
#include <numpy/arrayobject.h>
#include <hist2d.h>

static char module_docstring[] =
    "This module provides an interface for calculating 2-dimensional Histograms using C without weightings.";
static char chi2_docstring[] =
    "Calculate 2d-Histogram using 2 arrays and binning dimensions, returns 2d-matrix, x-vector, and a y-vector.";

// self object points to the module and the args object is a Python tuple of input arguments
static PyObject *hist2d_hist2d(Pyobject, *self, Pyobject *args) 

// specify member of module
static PyMethodDef module_methods[] = {
    {"hist2d", hist2d_hist2d, METH_VARARGS, chi2_docstring},
    {NULL, NULL, 0, NULL}
};



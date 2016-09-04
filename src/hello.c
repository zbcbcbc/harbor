#include <Python.h>
#include <string.h>


static PyObject* message(PyObject *self, PyObject *args)
{
	char* src, res[100];
	if (!PyArg_Parse(args, "(s)", &src))	return NULL;
	
	strcpy(res, "Hello, ");
	strcat(res, src);
	strcat(res, "\r\n");
	return Py_BuildValue("s", res);
}

static struct PyMethodDef methods[] = 
{
	{"message", message, 1, "descript of message"},
	{NULL, NULL, 0, NULL}
};


PyMODINIT_FUNC inithello()
{
	(void)Py_InitModule("hello", methods);
}




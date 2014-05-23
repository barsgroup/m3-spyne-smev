# -*- coding: utf-8 -*-

"""
controller.py

:Created: 3/12/14
:Author: timic
"""

import objectpack

observer = objectpack.observer.Observer()
controller = objectpack.observer.ObservableController(
    url='wsfactory', observer=observer)
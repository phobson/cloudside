import os


def source(source):
    """ checks that a *source* value is valid """
    if source.lower() not in ('wunderground', 'asos', 'wunder_nonairport'):
        raise ValueError('source must be one of "wunderground" or "asos"')


def step(step):
    """ checks that a *step* value is valid """
    if step.lower() not in ('raw', 'flat', 'compile'):
        raise ValueError('step must be one of "raw" or "flat"')


def file_status(filename):
    """ confirms that a raw file isn't empty """
    try:
        testfile = open(filename, 'r')
        lines = testfile.readlines()
        testfile.close()
        if len(lines) > 1:
            status = 'ok'
        else:
            status = 'bad'

    except IOError:
        status = 'not there'

    return status


def data_directory(subdirs):
    """ checks to see that a directory exists. if not, it makes it. """
    if not os.path.exists(subdirs[0]):
        os.mkdir(subdirs[0])

    if len(subdirs) > 1:
        topdir = [os.path.join(subdirs[0], subdirs[1])]
        for sd in subdirs[2:]:
            topdir.append(sd)
        data_directory(topdir)

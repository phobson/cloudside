import sys
import matplotlib
from matplotlib import style

import cloudside

matplotlib.use('agg')
style.use('classic')

status = cloudside.teststrict(*sys.argv[1:])
sys.exit(status)

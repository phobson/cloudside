import sys
import matplotlib
from matplotlib import style

import cloudside

matplotlib.use("agg")
style.use("classic")

if "--strict" in sys.argv:
    sys.argv.remove("--strict")
    status = cloudside.teststrict(*sys.argv[1:])
else:
    status = cloudside.test(*sys.argv[1:])

sys.exit(status)

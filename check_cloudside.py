import sys
import matplotlib; matplotlib.use('agg')

import cloudside


status = cloudside.test(*sys.argv[1:])
sys.exit(status)

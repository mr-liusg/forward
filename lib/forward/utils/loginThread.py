# This file is part of Forward.
#
# Forward is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Forward is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
-----Introduction-----
[Core][Forward] Login method thread function, used for the initialize multithread step
"""

import six


def loginThread(instance):
    # Login method thread function, used for the initialize multithread step
    if not instance.isLogin:
        result = instance.login()
        if not result['status']:
            six.print_('[Login Error]: %s :%s' % (instance.ip, result['errLog']))
            # print '[Login Error]: %s :%s' % (instance.ip, result['errLog'])
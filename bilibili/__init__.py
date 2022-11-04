"""
This file is part of bilibili-console.

bilibili-console is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

bilibili-console is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with bilibili-console. If not, see <https://www.gnu.org/licenses/>.
"""

import os


def init():
    if os.path.exists("init"):
        return False
    print("正在初始化LBCC.")
    if not os.path.exists("cached"):
        os.mkdir("cached")
    if not os.path.exists("users"):
        os.mkdir("users")
    with open("init", "w"):
        pass
    print("初始化完成.")
    return True

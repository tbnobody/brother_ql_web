import subprocess
import sys
from collections import defaultdict


class Fonts:
    def __init__(self):
        self.fonts = defaultdict(dict)

    def parse_fonts(self, raw):
        """ adds the found fonts the the fonts list
        :param raw: command to be run to get the raw font list from the system
        :return: true if fonts were added false if not
        """

        if raw.returncode != 0:
            return {'error': 'an error occurred while processing the fonts'}

        for line in raw.stdout.decode('utf-8').split('\n'):
            font = line.split(':')
            if len(font) < 3:
                continue
            # ignore non true type fonts
            if '.ttf' in font[0] or '.otf' in font[0]:
                fontname = font[1].replace('\\', '')
                fontpath = font[0].strip()
                fontstyle = font[2][6:].strip().split(',')[0]

                if ',' in fontname:
                    fontname = fontname.split()[0]
                fontname = fontname.strip()

                self.fonts[fontname][fontstyle] = fontpath
            else:
                pass

    def scan_global_fonts(self):
        """ Get a list of all fonts that are available to the user who runs this
        :return: raw output of the command fc-list
        """
        command = ['fc-list']
        try:
            raw = subprocess.run(command, stdout=subprocess.PIPE)
        except FileNotFoundError:
            print('fc-list not found', file=sys.stderr)
            sys.exit(2)

        self.parse_fonts(raw)

    def scan_fonts_folder(self, folder):
        """ Get a list of all fonts that are available to the user who runs this
        :return: raw output of the command fc-list
        """
        cmd = ['fc-scan', '--format',
               '%{file}:%{family}:style=%{style}\n', folder]
        try:
            raw = subprocess.run(cmd, stdout=subprocess.PIPE)
        except FileNotFoundError:
            print('fc-list not found', file=sys.stderr)
            sys.exit(2)

        self.parse_fonts(raw)

    def fontlist(self):
        return sorted(self.fonts, key=str.lower)

    def fonts_available(self):
        if len(self.fonts) == 0:
            return False
        else:
            return len(self.fonts)

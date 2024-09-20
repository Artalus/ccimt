import platform
import time

from conan import ConanFile
from conan.tools.files import copy


class Pkg(ConanFile):
    name = 'ccimt-test-local'
    description = 'Empty package to test changes in CI'
    settings = 'os', 'arch', 'compiler', 'build_type'

    def requirements(self):
        self.requires('zlib/1.2.13')

    def build(self):
        with open('file.pkg', 'w') as f, open(__file__, 'rb') as recipe:
            f.write(f'version={self.version}\n\n{self.info.settings.dumps()}\n')
            plat = platform.system()
            self.output.info(f'PLATFORM: {plat}')
            if plat == 'Windows':
                self.output.info('Imitating windows non-deterministic builds')
                f.writelines(f'\ntime={time.time()}\n')

    def package(self):
        copy(self, '*.pkg', src=self.build_folder, dst=self.package_folder)

from conan import ConanFile
class Pkg(ConanFile):
    name = 'ccimt-test-fork'
    settings = "os", "arch", "compiler", "build_type"
    def build( self ):
        pass

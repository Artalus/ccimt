from pathlib import Path

from ccimt.config import RecipeLintersSet


class Test_RecipeLintersSet:
    class Test_PatternMatch:
        class Test_Without_Exclude:
            def sut(self, pattern: str) -> RecipeLintersSet:
                return RecipeLintersSet(pattern=pattern, exclude=None, commands=[])

            def test_simple_pattern_matches_simple_file(self) -> None:
                assert self.sut('file.py').file_matches_patterns(Path('file.py'))

            def test_simple_pattern_does_not_match_subfolder(self) -> None:
                assert not self.sut('file.py').file_matches_patterns(Path('folder/file.py'))

            def test_foldered_pattern_does_not_match_simple_file(self) -> None:
                assert not self.sut('folder/file.py').file_matches_patterns(Path('file.py'))

            def test_foldered_pattern_matches_subfolder(self) -> None:
                assert self.sut('folder/file.py').file_matches_patterns(Path('folder/file.py'))

            def test_foldered_pattern_does_not_match_different_subfolder(self) -> None:
                assert not self.sut('folder/file.py').file_matches_patterns(Path('another/file.py'))

            def test_wildcarded_pattern_does_not_match_simple_file(self) -> None:
                assert not self.sut('*/file.py').file_matches_patterns(Path('file.py'))

            def test_wildcarded_pattern_matches_subfolder(self) -> None:
                assert self.sut('*/file.py').file_matches_patterns(Path('folder/file.py'))

        class Test_With_Exclude:
            def sut(self, pattern: str) -> RecipeLintersSet:
                return RecipeLintersSet(pattern=pattern, exclude='ignore/*', commands=[])

            def test_simple_pattern_matches_simple_file(self) -> None:
                assert self.sut('file.py').file_matches_patterns(Path('file.py'))

            def test_wildcarded_pattern_matches_valid_subfolder(self) -> None:
                assert self.sut('*/file.py').file_matches_patterns(Path('folder/file.py'))

            def test_wildcarded_pattern_does_not_match_ignored_file(self) -> None:
                assert not self.sut('*/file.py').file_matches_patterns(Path('ignore/file.py'))

"""
Unit tests for the BoxLang version info feature (version_info.py) and executable resolution.
"""

import os
from unittest.mock import MagicMock, patch

from tests.expectations import expect


def _info(**overrides):
    info = {
        'installed': True, 'version': '1.18.0+1', 'executable': '/home/u/.local/bin/boxlang',
        'source': 'candidate', 'kind': 'quick-user', 'kind_label': 'Quick installer (user)',
        'project_root': '/work/app', 'boxlang_home': ('/home/u/.boxlang', 'default'),
        'tried': ['/usr/local/bin/boxlang'], 'project_config': False, 'bvm': None,
    }
    info.update(overrides)
    return info


class TestClassifyInstall:
    def test_bvm(self, tmp_path):
        from src import version_info
        env = {'BVM_HOME': str(tmp_path / 'bvm')}
        key, _ = version_info.classify_install(str(tmp_path / 'bvm' / 'current' / 'bin' / 'boxlang'), 'candidate', env)
        expect(key).to_be('bvm')
        key, _ = version_info.classify_install('/Users/u/.bvm/current/bin/boxlang', 'candidate', {})
        expect(key).to_be('bvm')

    def test_homebrew(self):
        from src import version_info
        key, label = version_info.classify_install('/opt/homebrew/bin/boxlang', 'candidate', {})
        expect(key).to_be('homebrew')
        expect(label).to_be('Homebrew')

    def test_quick_installer_user_and_system(self):
        from src import version_info
        home = os.path.expanduser('~')
        expect(version_info.classify_install(home + '/.local/bin/boxlang', 'candidate', {})[0]).to_be('quick-user')
        expect(version_info.classify_install(home + '/.local/boxlang/bin/boxlang', 'candidate', {})[0]).to_be('quick-user')
        expect(version_info.classify_install('/usr/local/bin/boxlang', 'candidate', {})[0]).to_be('quick-system')

    def test_windows(self):
        from src import version_info
        expect(version_info.classify_install('c:\\boxlang\\bin\\boxlang.bat', 'candidate', {})[0]).to_be('windows')
        expect(version_info.classify_install('C:\\BoxLang\\bin\\boxlang.bat', 'setting', {})[0]).to_be('windows')

    def test_path_and_other(self):
        from src import version_info
        expect(version_info.classify_install('/somewhere/bin/boxlang', 'path', {})[0]).to_be('path')
        expect(version_info.classify_install('/opt/custom/boxlang', 'setting', {})[0]).to_be('other')

    def test_describe_source(self):
        from src import version_info
        expect(version_info.describe_source('setting', 'other', 'Custom location')).to_contain('boxlang_executable_path')
        expect(version_info.describe_source('path', 'path', 'PATH')).to_contain('PATH')
        expect(version_info.describe_source('candidate', 'homebrew', 'Homebrew')).to_be('Homebrew')


class TestBvm:
    def test_bvm_home_absent_and_present(self, tmp_path):
        from src import version_info
        expect(version_info.bvm_home({'BVM_HOME': str(tmp_path / 'missing')})).to_be_none()
        (tmp_path / 'bvm').mkdir()
        expect(version_info.bvm_home({'BVM_HOME': str(tmp_path / 'bvm')})).to_be(str(tmp_path / 'bvm'))

    def test_read_bvmrc_walks_up_and_skips_comments(self, tmp_path):
        from src import version_info
        (tmp_path / '.bvmrc').write_text('# project version\n\n1.17.6\n')
        nested = tmp_path / 'src' / 'models'
        nested.mkdir(parents=True)
        expect(version_info.read_bvmrc(str(nested))).to_be(('1.17.6', str(tmp_path / '.bvmrc')))

    def test_read_bvmrc_none(self, tmp_path):
        from src import version_info
        expect(version_info.read_bvmrc(str(tmp_path))).to_be_none()

    def test_current_and_installed(self, tmp_path):
        from src import version_info
        versions = tmp_path / 'versions'
        for name in ('1.17.6', '1.18.0', '1.9.0'):
            (versions / name).mkdir(parents=True)
        os.symlink(str(versions / '1.18.0'), str(tmp_path / 'current'))
        os.symlink(str(versions / '1.18.0'), str(versions / 'latest'))
        expect(version_info.bvm_current(str(tmp_path))).to_be('1.18.0')
        expect(version_info.bvm_installed(str(tmp_path))).to_be(['1.9.0', '1.17.6', '1.18.0'])

    def test_current_unknown_without_link(self, tmp_path):
        from src import version_info
        expect(version_info.bvm_current(str(tmp_path))).to_be_none()
        expect(version_info.bvm_installed(str(tmp_path))).to_be_empty()

    def test_mismatch_rules(self):
        from src import version_info
        expect(version_info.bvmrc_mismatch('1.18.0+1', '1.17.6')).to_be_true()
        expect(version_info.bvmrc_mismatch('1.18.0+1', '1.18.0')).to_be_false()
        expect(version_info.bvmrc_mismatch('1.18.0', 'latest')).to_be_false()
        expect(version_info.bvmrc_mismatch('1.18.0', 'snapshot')).to_be_false()
        expect(version_info.bvmrc_mismatch('', '1.17.6')).to_be_false()

    def test_status_suffix_only_for_bvm_mismatch(self, tmp_path):
        from src import version_info
        (tmp_path / 'bvm').mkdir()
        (tmp_path / '.bvmrc').write_text('1.17.6\n')
        file_path = str(tmp_path / 'a.bx')
        with patch.object(version_info, 'bvm_home', return_value=str(tmp_path / 'bvm')):
            expect(version_info.status_suffix(file_path, '1.18.0')).to_be(' (.bvmrc 1.17.6)')
            expect(version_info.status_suffix(file_path, '1.17.6')).to_be('')
        with patch.object(version_info, 'bvm_home', return_value=None):
            expect(version_info.status_suffix(file_path, '1.18.0')).to_be('')

    def test_status_suffix_is_safe_with_bad_input(self):
        from src import version_info
        expect(version_info.status_suffix(None, '1.18.0')).to_be('')
        expect(version_info.status_suffix(MagicMock(), '1.18.0')).to_be('')


class TestBoxlangHome:
    def test_env_and_default(self):
        from src import version_info
        expect(version_info.boxlang_home({'BOXLANG_HOME': '/x'})).to_be(('/x', 'env'))
        path, source = version_info.boxlang_home({})
        expect(source).to_be('default')
        expect(path.endswith('.boxlang')).to_be_true()


class TestReport:
    def test_quick_installer_user_sees_no_bvm_section(self):
        from src import version_info, boxlang_cli
        boxlang_cli._boxlang_version = '1.18.0+1'
        text = version_info.format_report(_info())
        expect(text).to_contain('Version      : 1.18.0+1')
        expect(text).to_contain('Quick installer (user)')
        expect(text).to_contain('install-boxlang --check-update')
        expect('BVM' in text).to_be_false()
        expect('bvmrc' in text).to_be_false()

    def test_bvm_section_with_mismatch(self):
        from src import version_info, boxlang_cli
        boxlang_cli._boxlang_version = '1.18.0+1'
        bvm = {'home': '/h/.bvm', 'current': '1.18.0', 'installed': ['1.17.6', '1.18.0'], 'bvmrc': ('1.17.6', '/work/app/.bvmrc'), 'mismatch': True}
        text = version_info.format_report(_info(kind='bvm', kind_label='BVM', bvm=bvm))
        expect(text).to_contain('Global (bvm current) : 1.18.0')
        expect(text).to_contain('Project (.bvmrc)     : 1.17.6')
        expect(text).to_contain('differs from the active version')
        expect(text).to_contain('1.17.6, 1.18.0')
        expect(text).to_contain('bvm list-remote')

    def test_bvm_without_bvmrc(self):
        from src import version_info, boxlang_cli
        boxlang_cli._boxlang_version = '1.18.0'
        bvm = {'home': '/h/.bvm', 'current': '1.18.0', 'installed': [], 'bvmrc': None, 'mismatch': False}
        text = version_info.format_report(_info(kind='bvm', kind_label='BVM', bvm=bvm))
        expect(text).to_contain('Project (.bvmrc)     : none')
        expect(text).to_contain('none found')

    def test_old_boxlang_is_flagged(self):
        from src import version_info, boxlang_cli
        boxlang_cli._boxlang_version = '1.16.0'
        text = version_info.format_report(_info(version='1.16.0'))
        expect(text).to_contain('syntax check unavailable (needs BoxLang 1.17+)')

    def test_not_installed_lists_locations(self):
        from src import version_info
        text = version_info.format_report(_info(installed=False, executable='boxlang', tried=['/opt/homebrew/bin/boxlang', '/usr/local/bin/boxlang']))
        expect(text).to_contain('NOT found')
        expect(text).to_contain('/opt/homebrew/bin/boxlang')
        expect(text).to_contain('boxlang_executable_path')

    def test_env_home_and_project_config_shown(self):
        from src import version_info, boxlang_cli
        boxlang_cli._boxlang_version = '1.18.0'
        text = version_info.format_report(_info(boxlang_home=('/data/bx', 'env'), project_config=True))
        expect(text).to_contain('/data/bx (from the environment)')
        expect(text).to_contain('.boxlang.json : found')

    def test_no_project_folder(self):
        from src import version_info, boxlang_cli
        boxlang_cli._boxlang_version = '1.18.0'
        text = version_info.format_report(_info(project_root=None))
        expect(text).to_contain('(no project folder open)')


class TestCollect:
    def test_collect_without_bvm(self, tmp_path):
        from src import version_info, boxlang_cli
        (tmp_path / '.boxlang.json').write_text('{}')
        with patch.object(boxlang_cli, 'redetect', return_value=(True, '1.18.0', '/opt/homebrew/bin/boxlang', 'candidate')), \
                patch.object(version_info, 'bvm_home', return_value=None):
            info = version_info.collect(str(tmp_path), {})
        expect(info['kind']).to_be('homebrew')
        expect(info['bvm']).to_be_none()
        expect(info['project_config']).to_be_true()

    def test_collect_with_bvm(self, tmp_path):
        from src import version_info, boxlang_cli
        home = tmp_path / 'bvm'
        (home / 'versions' / '1.17.6').mkdir(parents=True)
        (tmp_path / 'proj').mkdir()
        (tmp_path / 'proj' / '.bvmrc').write_text('1.17.6')
        with patch.object(boxlang_cli, 'redetect', return_value=(True, '1.18.0', str(home / 'current' / 'bin' / 'boxlang'), 'candidate')), \
                patch.object(version_info, 'bvm_home', return_value=str(home)):
            info = version_info.collect(str(tmp_path / 'proj'), {'BVM_HOME': str(home)})
        expect(info['kind']).to_be('bvm')
        expect(info['bvm']['bvmrc'][0]).to_be('1.17.6')
        expect(info['bvm']['mismatch']).to_be_true()
        expect(info['bvm']['installed']).to_be(['1.17.6'])


class TestProjectRoot:
    def test_prefers_open_folder_containing_file(self):
        from src import version_info
        view = MagicMock()
        view.file_name.return_value = '/work/app/models/User.bx'
        window = MagicMock()
        window.folders.return_value = ['/other', '/work/app']
        expect(version_info.project_root_for(window, view)).to_be('/work/app')

    def test_falls_back_to_file_dir_then_first_folder(self):
        from src import version_info
        view = MagicMock()
        view.file_name.return_value = '/tmp/x/a.bx'
        window = MagicMock()
        window.folders.return_value = []
        expect(version_info.project_root_for(window, view)).to_be('/tmp/x')
        window.folders.return_value = ['/work/app']
        expect(version_info.project_root_for(window, None)).to_be('/work/app')


class TestExecutableResolution:
    def test_setting_wins(self, mock_sublime_settings):
        from src import boxlang_cli
        mock_sublime_settings['boxlang_executable_path'] = '/custom/boxlang'
        expect(boxlang_cli.resolve_executable()).to_be(('/custom/boxlang', 'setting'))

    def test_candidate_then_path_then_missing(self, mock_sublime_settings):
        from src import boxlang_cli
        with patch.object(boxlang_cli.os.path, 'isfile', side_effect=lambda p: p == '/opt/homebrew/bin/boxlang'):
            expect(boxlang_cli.resolve_executable()).to_be(('/opt/homebrew/bin/boxlang', 'candidate'))
        with patch.object(boxlang_cli.os.path, 'isfile', return_value=False), patch.object(boxlang_cli.shutil, 'which', return_value='/x/bin/boxlang'):
            expect(boxlang_cli.resolve_executable()).to_be(('/x/bin/boxlang', 'path'))
        with patch.object(boxlang_cli.os.path, 'isfile', return_value=False), patch.object(boxlang_cli.shutil, 'which', return_value=None):
            expect(boxlang_cli.resolve_executable()).to_be(('boxlang', 'missing'))

    def test_homebrew_path_is_a_candidate(self):
        from src import boxlang_cli
        expect('/opt/homebrew/bin/boxlang' in boxlang_cli.executable_candidates()).to_be_true()

    def test_get_boxlang_path_is_none_when_missing(self, mock_sublime_settings):
        from src import build_helpers, boxlang_cli
        with patch.object(boxlang_cli, 'resolve_executable', return_value=('boxlang', 'missing')):
            expect(build_helpers.get_boxlang_path()).to_be_none()
        with patch.object(boxlang_cli, 'resolve_executable', return_value=('/x/boxlang', 'path')):
            expect(build_helpers.get_boxlang_path()).to_be('/x/boxlang')

    def test_redetect_updates_state_without_callbacks(self, mock_sublime_settings):
        from src import boxlang_cli
        callback = MagicMock()
        boxlang_cli._detection_callbacks.append(callback)
        try:
            with patch.object(boxlang_cli, 'resolve_executable', return_value=('/x/boxlang', 'path')), \
                    patch.object(boxlang_cli, '_run_command', return_value=(0, 'BoxLang 1.18.0+1\n', '')):
                result = boxlang_cli.redetect()
        finally:
            boxlang_cli._detection_callbacks.remove(callback)
        expect(result).to_be((True, '1.18.0+1', '/x/boxlang', 'path'))
        callback.assert_not_called()

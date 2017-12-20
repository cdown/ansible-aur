#!/usr/bin/env python2

from ansible.module_utils.basic import *


TOOL_CMD_MAP = {
    'pacaur': ['pacaur', '--noconfirm', '--noedit'],
    'yaourt': ['yaourt', '--noconfirm'],
}


def package_installed(module, package_name):
    cmd = ['pacman', '-Q', package_name]
    exit_code, _, _ = module.run_command(cmd, check_rc=False)
    return exit_code == 0


def update_packages(module, tool, auronly):
    assert tool in TOOL_CMD_MAP

    cmd = ['env', 'LC_ALL=C'] + TOOL_CMD_MAP[tool] + ['-Su']
    if auronly:
        cmd += ['--aur']
    rc, stdout, stderr = module.run_command(cmd, check_rc=True)

    module.exit_json(
        changed='there is nothing to do' not in stdout,
        msg='updated packages',
    )


def install_packages(module, package_name, tool, update, auronly):
    if package_installed(module, package_name):
        module.exit_json(
            changed=False,
            msg='package already installed',
        )

    assert tool in TOOL_CMD_MAP

    options = '-S'

    if update:
        options += 'u'

    cmd = TOOL_CMD_MAP[tool] + [options, package_name]
    if auronly:
        cmd += ['--aur']
    module.run_command(cmd, check_rc=True)

    module.exit_json(
        changed=True,
        msg='installed package',
    )


def remove_packages(module, package_name, recurse, nosave):
    if not package_installed(module, package_name):
        module.exit_json(
            changed=False,
            msg='package not installed',
        )

    options = '-R'

    if nosave:
        options += 'n'

    if recurse:
        options += 's'

    cmd = ['pacman', '--noconfirm', options, package_name]
    module.run_command(cmd, check_rc=True)

    module.exit_json(
        changed=True,
        msg='removed package',
    )


def main():
    module = AnsibleModule(
        argument_spec={
            'name': {
                'required': False,
            },
            'state': {
                'default': 'present',
                'choices': ['present', 'absent'],
            },
            'tool': {
                'default': 'pacaur',
                'choices': ['pacaur', 'yaourt'],
            },
            'recurse': {
                'default': True,
                'type': 'bool',
            },
            'nosave': {
                'default': True,
                'type': 'bool',
            },
            'update': {
                'default': False,
                'type': 'bool',
            },
            'auronly': {
                'default': True,
                'type': 'bool',
            },
        },
        required_one_of=[['name', 'update']],
    )

    params = module.params

    if params['update'] and not params['name']:
        update_packages(module, params['tool'], params['auronly'])
    elif params['state'] == 'present':
        install_packages(
            module, params['name'], params['tool'], params['update'],
            params['auronly'],
        )
    elif params['state'] == 'absent':
        remove_packages(
            module, params['name'], params['recurse'], params['nosave'],
        )


if __name__ == '__main__':
    main()

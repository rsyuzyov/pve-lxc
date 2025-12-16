#!/bin/bash
# Bash completion для pve-lxc

_pve_lxc_completion() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Команды первого уровня
    local commands="apps bootstrap create deploy destroy host ip list"
    
    # Подкоманды host
    local host_commands="add list remove set-default test"

    # Если это первый аргумент после pve-lxc
    if [[ $COMP_CWORD -eq 1 ]]; then
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
        return
    fi

    # Если предыдущее слово - host
    if [[ ${COMP_WORDS[1]} == "host" && $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=($(compgen -W "$host_commands" -- "$cur"))
        return
    fi

    # Опции для команд
    case ${COMP_WORDS[1]} in
        create)
            COMPREPLY=($(compgen -W "--name -n --cores -c --memory -m --disk -d --ip --gateway -g --gpu --json --config -C --help" -- "$cur"))
            ;;
        destroy)
            COMPREPLY=($(compgen -W "--force -f --json --config -C --help" -- "$cur"))
            ;;
        deploy)
            COMPREPLY=($(compgen -W "--app -a --container -c --create --ctid --name -n --cores --memory --disk --ip --gateway --json --config -C --help" -- "$cur"))
            ;;
        bootstrap)
            COMPREPLY=($(compgen -W "--help" -- "$cur"))
            ;;
        ip)
            COMPREPLY=($(compgen -W "--help" -- "$cur"))
            ;;
        list)
            COMPREPLY=($(compgen -W "--json --help" -- "$cur"))
            ;;
        apps)
            COMPREPLY=($(compgen -W "--help" -- "$cur"))
            ;;
        host)
            case ${COMP_WORDS[2]} in
                add)
                    COMPREPLY=($(compgen -W "--hostname -h --user -u --port -p --key -k --help" -- "$cur"))
                    ;;
                list)
                    COMPREPLY=($(compgen -W "--verbose -v --help" -- "$cur"))
                    ;;
                test|remove|set-default)
                    COMPREPLY=($(compgen -W "--help" -- "$cur"))
                    ;;
            esac
            ;;
    esac
}

complete -F _pve_lxc_completion pve-lxc

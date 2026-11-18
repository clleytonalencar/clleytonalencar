# Otimização da ROM original — Realme C55 (RMX3710)

Sem root, sem desbloquear bootloader, sem perder garantia. Tudo é reversível.

## O que o `otimizar.sh` faz
1. Remove propaganda (Glance, revista da tela de bloqueio), telemetria e apps duplicados da Realme, lista em `pacotes.txt`
2. Reduz as animações para 0.5x
3. Limpa o cache de todos os apps
4. Recompila os apps (`speed-profile`), deixando a abertura mais rápida
5. Oferece reiniciar

O `restaurar.sh` desfaz tudo.

## Antes de começar (no celular)
1. Configurações > Sobre o telefone > Versão: toque 7x em **Número da versão**
2. Configurações > Configurações adicionais > **Opções do desenvolvedor** > ligue **Depuração USB**
   (e "Desativar monitoramento de permissões", se aparecer)

## Opção A — Com PC
- Windows: baixe o [Platform Tools](https://developer.android.com/tools/releases/platform-tools) e use o Git Bash ou WSL
- Linux: `sudo apt install adb`

Conecte o cabo, aceite o aviso "Permitir depuração USB" no celular e rode:
```bash
adb devices
bash otimizar.sh
```

## Opção B — Sem PC (só o celular)
1. Instale o **Termux** pelo F-Droid e rode `pkg install android-tools`
2. Em Opções do desenvolvedor, ligue **Depuração sem fio** e toque em "Parear com código"
3. No Termux (use tela dividida): `adb pair 127.0.0.1:PORTA_DO_PAREAMENTO CODIGO`
   e depois `adb connect 127.0.0.1:PORTA_MOSTRADA_NA_TELA`
4. Copie esta pasta para o celular e rode `bash otimizar.sh`

Alternativa sem comandos: **Shizuku** + **Canta** (Play Store / F-Droid) para remover os apps tocando na lista.

## Ajustes manuais que valem a pena
- **Expansão de RAM**: Configurações > Sobre o telefone > RAM > desligar (no G88 ela mais atrapalha)
- **Taxa de atualização**: Tela > 90 Hz fica fluido; "Automática" economiza bateria
- Deixar pelo menos **20% do armazenamento livre**
- Usar versões Lite (Facebook Lite etc.) quando existir
- Atualizar o sistema pelo menu oficial antes de otimizar

## O que NÃO fazer
- Não remova pacotes `com.oplus.*`/`com.android.*` fora desta lista ("debloat agressivo" de vídeos causa bootloop)
- Não use apps de "limpeza/booster de RAM": eles deixam o celular mais lento

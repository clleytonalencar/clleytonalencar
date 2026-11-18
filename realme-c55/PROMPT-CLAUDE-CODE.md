# Prompt para o Claude Code no Mac

Com o celular conectado por USB e `adb devices` mostrando o aparelho como `device`,
abra o Terminal numa pasta vazia, rode `claude` e cole o texto abaixo.

```text
Você vai otimizar um Realme C55 (RMX3710) conectado neste Mac por USB, usando ADB. Ele está com a ROM original da Realme. Objetivo: transformá-lo num aparelho leve, fluido e o mais próximo possível de um Android puro, para usar só WhatsApp, WhatsApp Business, Instagram, apps de banco e gov.br. Não uso jogos e quase não uso a câmera.

REGRAS QUE NÃO PODEM SER QUEBRADAS
- Nada de root, desbloqueio de bootloader, flash de partição, fastboot, mtkclient ou ROM customizada. Bancos e gov.br precisam do aparelho original e bloqueado.
- Remover apps só com "pm uninstall --user 0" (reversível). Nunca "pm uninstall" sem --user 0, nunca "rm" em partições do sistema.
- Nunca remover nem desativar: com.google.android.gms, com.google.android.gsf, com.android.vending, com.google.android.webview, com.android.chrome, com.android.phone, com.android.settings, com.android.systemui, com.android.providers.*, com.android.permissioncontroller, com.google.android.permissioncontroller, com.android.packageinstaller, com.google.android.packageinstaller, o launcher em uso, o teclado em uso, com.oplus.romupdate, com.oplus.athena, com.oplus.battery, com.oplus.securitypermission, qualquer pacote com "telephony", "ims", "mms", "wifi", "bluetooth", "nfc", "camera", "biometric", "fingerprint", "face", "keychain", "cert", "security" ou "permission" no nome.
- Na dúvida sobre um pacote, NÃO remova: liste como "incerto" e me pergunte.
- Antes de remover qualquer coisa, me mostre a lista e espere eu responder "pode".

ETAPAS
1. Diagnóstico (só leitura): instale o adb com Homebrew se faltar (brew install --cask android-platform-tools). Confirme com adb devices e getprop ro.product.model que é um RMX3710. Mostre: versão do Android e da Realme UI (ro.build.display.id), patch de segurança, RAM total, armazenamento livre (df /data), bateria (dumpsys battery) e os 15 processos que mais usam memória (dumpsys meminfo).
2. Backup: crie a pasta ./realme-c55-backup e salve nela a saída de "pm list packages -f", "pm list packages -d", "pm list packages -3" e os valores atuais de window_animation_scale, transition_animation_scale e animator_duration_scale.
3. Plano: com base na lista real de pacotes, monte uma tabela com três grupos: REMOVER (propaganda como Glance e com.heytap.pictorial; telemetria como com.nearme.statistics.rom e com.oplus.statistics.rom; serviços do Facebook e Netflix pré-instalados; loja, navegador, música e vídeo da Realme/HeyTap; Central de Jogos e Espaço de Jogos; Espaço Infantil; apps instalados de fábrica que não são de sistema), MANTER (o que está nas regras) e INCERTO (me pergunte). Para cada item diga em poucas palavras o que é. Pare e espere minha resposta.
4. Execução: remova os pacotes aprovados, um por vez, mostrando o resultado. Salve em ./realme-c55-backup/removidos.txt a lista do que saiu e crie ./realme-c55-backup/restaurar.sh que reinstala tudo com "cmd package install-existing".
5. Ajustes: animações em 0.5x (settings put global para as três escalas). Limpe caches com "pm trim-caches 999G". Recompile os apps com "cmd package compile -m speed-profile -a" e depois "cmd package bg-dexopt-job" (avise que leva de 10 a 30 minutos e que o celular deve estar na tomada).
6. Checklist manual: me passe, em passos curtos, o que fazer na tela do celular: desligar a Expansão de RAM, deixar a tela em 90 Hz, desligar a inicialização automática de tudo exceto WhatsApp, WhatsApp Business e bancos, e desligar o download automático de mídia do WhatsApp em dados móveis.
7. Verificação: reinicie com adb reboot, espere o aparelho voltar (adb wait-for-device e sys.boot_completed = 1) e repita o diagnóstico da etapa 1 mostrando antes x depois (memória livre, armazenamento, número de pacotes ativos). Me peça para abrir WhatsApp, WhatsApp Business, Instagram, um app de banco e o gov.br e confirmar que tudo funciona. Se algo quebrar, use o restaurar.sh para trazer de volta o último grupo removido.
8. Relatório final: salve ./realme-c55-backup/RELATORIO.md com tudo que foi feito, o que foi removido, o antes x depois e como reverter.

Fale comigo em português, de forma simples, e explique cada etapa antes de executar.
```

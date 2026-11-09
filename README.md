# Jogar novamente

Aplicativo Windows em **Python + Tkinter**, com um controle Xbox 360 virtual via
`vgamepad`. Implementa a **abordagem 2**: enquanto ligado e com o Fortnite em
primeiro plano, aperta e solta **Y** a cada intervalo aleatório de **3 a 10 segundos**.
O primeiro comando também aguarda um intervalo completo. Não é a tecla Y do teclado.

Python mantém a interface simples e exige apenas uma dependência externa.
XInput é uma API de leitura de controles; o dispositivo virtual fornece os comandos
que o jogo lê como um controle Xbox.

## Usar

1. Tenha Python **3.10 ou superior**, com Tkinter e o launcher `py`, no Windows 10/11.
2. Execute **`instalar.bat`** uma vez. As dependências ficam em `.venv`.
3. Para envio real, o driver **ViGEmBus** precisa estar instalado. O instalador
   deste projeto não instala nem altera drivers. Se necessário, use somente a
   [distribuição oficial](https://github.com/nefarius/ViGEmBus/releases/tag/v1.22.0)
   e reinicie o Windows. O [projeto foi aposentado](https://github.com/nefarius/ViGEmBus),
   portanto não há garantia de compatibilidade com atualizações futuras.
4. Abra **`iniciar.bat`**. Ajuste mínimo e máximo se desejar. Para intervalo fixo
   de cinco segundos, coloque `5` nos dois campos.
5. Clique **Ligar**, volte ao Fortnite e use **F8** para ligar/desligar ou **F9**
   para parar. Os atalhos funcionam mesmo com a janela em segundo plano, salvo
   se outro aplicativo já tiver registrado essas teclas; nesse caso a interface avisa.
6. **Desligar**, **F9** e fechar a janela interrompem a espera e liberam o controle.

O aplicativo sempre abre desligado. Alterar os intervalos requer desligar primeiro.
Ao sair do jogo, o envio pausa; ao retornar, começa uma nova espera completa.
A verificação usa o executável do Fortnite em foco. Se o Windows impedir essa
verificação, o aplicativo permanece pausado.

## Testar sem enviar comandos

Marque **Simular sem enviar comandos**, clique Ligar e acompanhe o contador.
Esse modo dispensa o jogo, `vgamepad` e o driver, e usa os mesmos intervalos.
Também é possível abrir diretamente com `python app.py --simular`.

Para rodar os testes automatizados, sem gerar entradas reais:

```powershell
python -m unittest discover -s tests -v
```

## Limitações

- Não detecta o fim da partida: **Y também será enviado enquanto você joga**.
  Confirme se Y realmente executa “Jogar novamente” no seu layout. As imagens
  enviadas mostram o botão na tela, mas não confirmam o atalho de controle.
- Não inclui X ou movimentos dos analógicos; esses comandos podem executar
  ações indesejadas e não garantem proteção contra punições.
- **Não tira prints nem grava imagens**, então não há arquivos de captura a apagar.
- Um controle físico conectado pode ocupar o primeiro slot e impedir que o jogo
  responda ao controle virtual. A aceitação pelo Fortnite precisa ser verificada
  no seu ambiente. O aplicativo não contorna bloqueios do jogo ou do anticheat.
- Intervalos aleatórios **não eliminam o risco de banimento**. A Epic proíbe macros
  para automatizar ações em suas [regras competitivas](https://www.fortnite.com/competitive/rules-guidelines/rules-library/fortnite-global-championship-2026-official-rules?region=NAC).
  O temporizador aleatório implementa apenas a cadência solicitada.

API do controle: [documentação oficial do vgamepad](https://github.com/yannbouteiller/vgamepad).

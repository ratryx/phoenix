import pytest
import threading
import time
from modules.gui.window_controller import WindowController

class FakeWindow:
    def __init__(self, move_fail=False, min_fail=False, destroy_fail=False):
        self.move_calls = []
        self.minimize_calls = 0
        self.destroy_calls = 0
        self.move_fail = move_fail
        self.min_fail = min_fail
        self.destroy_fail = destroy_fail

    def move(self, x, y):
        if self.move_fail:
            raise RuntimeError("Fake move fail")
        self.move_calls.append((x, y))

    def minimize(self):
        if self.min_fail:
            raise RuntimeError("Fake min fail")
        self.minimize_calls += 1

    def destroy(self):
        if self.destroy_fail:
            raise RuntimeError("Fake destroy fail")
        self.destroy_calls += 1


def test_instanciado_sem_janela():
    # 1. controlador pode ser instanciado sem janela
    ctrl = WindowController()
    assert ctrl._window is None

def test_atribuicao_janela_privada():
    # 2 e 3. janela pode ser atribuída depois; armazenada privada
    ctrl = WindowController()
    win = FakeWindow()
    ctrl.set_window(win)
    assert ctrl._window is win
    assert not hasattr(ctrl, "window")

def test_iniciar_drag_estado():
    # 4. iniciar drag registra o estado
    ctrl = WindowController()
    ctrl.iniciar_drag(10, 20, 100, 200)
    assert ctrl._is_dragging is True
    assert ctrl._drag_start_mouse_x == 10
    assert ctrl._drag_start_mouse_y == 20
    assert ctrl._drag_start_win_x == 100
    assert ctrl._drag_start_win_y == 200

def test_mover_posicao_correta():
    # 5. mover janela calcula posição corretamente
    ctrl = WindowController()
    win = FakeWindow()
    ctrl.set_window(win)
    
    ctrl.iniciar_drag(50, 50, 100, 100)
    ctrl.mover_janela(60, 40)
    
    # Delta X: 60 - 50 = 10 -> new win X: 100 + 10 = 110
    # Delta Y: 40 - 50 = -10 -> new win Y: 100 - 10 = 90
    assert len(win.move_calls) == 1
    assert win.move_calls[0] == (110, 90)

def test_mover_sem_drag():
    # 6. mover sem drag ativo é controlado
    ctrl = WindowController()
    win = FakeWindow()
    ctrl.set_window(win)
    
    ctrl.mover_janela(60, 40) # drag=False
    assert len(win.move_calls) == 0

def test_parar_drag():
    # 7 e 8. parar drag encerra estado; parar duas vezes ok
    ctrl = WindowController()
    ctrl.iniciar_drag(0, 0, 0, 0)
    assert ctrl._is_dragging is True
    
    ctrl.parar_drag()
    assert ctrl._is_dragging is False
    
    ctrl.parar_drag()
    assert ctrl._is_dragging is False

def test_coordenadas_variadas():
    # 9, 10 e 11. inteiras, float e strings tratadas
    ctrl = WindowController()
    win = FakeWindow()
    ctrl.set_window(win)
    
    # Inteiros testados em test_mover_posicao_correta. Testando floats
    ctrl.iniciar_drag(10.5, 20.2, 100.9, 200.1)
    # int() trunca para 10, 20, 100, 200
    
    # Strings numericas
    ctrl.mover_janela("20", "30.5") 
    # int('20') -> 20. int('30.5') ira dar ValueError, que sera capturado e nao crashara
    
    # Como as chamadas capturam Exception, nao deve levantar erro
    assert ctrl._drag_start_mouse_x == 10

def test_coordenadas_invalidas():
    # 12. invalidas nao derrubam aplicacao
    ctrl = WindowController()
    win = FakeWindow()
    ctrl.set_window(win)
    
    # string invalida causara falha do int(), mas caira no except
    ctrl.iniciar_drag("asdf", 0, 0, 0)
    assert ctrl._is_dragging is False # Falhou logo de cara

    ctrl.iniciar_drag(0, 0, 0, 0)
    ctrl.mover_janela(None, None)
    assert len(win.move_calls) == 0

def test_delegacao_simples():
    # 13 e 14. minimizar e fechar delegam uma vez
    ctrl = WindowController()
    win = FakeWindow()
    ctrl.set_window(win)
    
    ctrl.minimizar()
    assert win.minimize_calls == 1
    
    ctrl.fechar()
    assert win.destroy_calls == 1

def test_metodos_sem_janela():
    # 15 e 16. minimizar e fechar sem janela é controlado
    ctrl = WindowController()
    # Sem win atribuida
    ctrl.minimizar()
    ctrl.fechar()
    # nao devem dar exception vazando

def test_excecoes_pywebview():
    # 17, 18, 19.
    ctrl = WindowController()
    win = FakeWindow(move_fail=True, min_fail=True, destroy_fail=True)
    ctrl.set_window(win)
    
    ctrl.iniciar_drag(0, 0, 0, 0)
    
    # Nenhuma deve espalhar traceback
    ctrl.mover_janela(10, 10)
    ctrl.minimizar()
    ctrl.fechar()

def test_controlador_nao_serializavel():
    # 20.
    ctrl = WindowController()
    import json
    with pytest.raises(TypeError):
        json.dumps(ctrl)
    
    # Assegura que ele n retorna dicts de estado 
    assert not isinstance(ctrl, dict)

def test_thread_safety_drag():
    # 21. Eventos concorrentes
    ctrl = WindowController()
    win = FakeWindow()
    ctrl.set_window(win)
    
    def worker():
        for i in range(100):
            ctrl.iniciar_drag(i, i, 100, 100)
            ctrl.mover_janela(i+1, i+1)
            ctrl.parar_drag()
            time.sleep(0.001)
            
    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    # Nao deve haver corrupcao destrutiva nem crashes
    assert len(win.move_calls) > 0

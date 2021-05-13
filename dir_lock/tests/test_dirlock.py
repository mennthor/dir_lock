from threading import Thread
import time


def test_dirlock(tmp_path):
    from dir_lock import DirLock

    def write(name):
        with DirLock(tmp_path / ".lock"):
            with open(tmp_path / name, "w") as f:
                f.write("hello")
            time.sleep(2)

    thread_a = Thread(target=write, args=("a.txt", ))
    thread_b = Thread(target=write, args=("b.txt", ))

    print([str(p) for p in tmp_path.iterdir()])

    thread_a.start()
    #  give a a chance to acquire the lock for determinism
    time.sleep(0.1)

    thread_b.start()

    assert (tmp_path / ".lock").is_file()
    assert (tmp_path / "a.txt").is_file()
    assert not (tmp_path / "b.txt").is_file()

    # wait until completion
    for t in [thread_a, thread_b]:
        t.join()

    assert not (tmp_path / ".lock").is_file()
    assert (tmp_path / "b.txt").is_file()

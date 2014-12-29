try:
    import queue
except ImportError:
    import Queue as queue
    
try:
    import threading
except ImportError: #pragma: no cover
    threading = None

if threading:
    class QueueListener(object):
        """
        This class implements an internal threaded listener which watches for
        LogRecords being added to a queue, removes them and passes them to a
        list of handlers for processing.
        """
        _sentinel = None

        def __init__(self, queue, *handlers):
            """
            Initialise an instance with the specified queue and
            handlers.
            """
            self.queue = queue
            self.handlers = handlers
            self._stop = threading.Event()
            self._thread = None

        def dequeue(self, block):
            """
            Dequeue a record and return it, optionally blocking.

            The base implementation uses get. You may want to override this method
            if you want to use timeouts or work with custom queue implementations.
            """
            return self.queue.get(block)

        def start(self):
            """
            Start the listener.

            This starts up a background thread to monitor the queue for
            LogRecords to process.
            """
            self._thread = t = threading.Thread(target=self._monitor)
            t.setDaemon(True)
            t.start()

        def prepare(self , record):
            """
            Prepare a record for handling.

            This method just returns the passed-in record. You may want to
            override this method if you need to do any custom marshalling or
            manipulation of the record before passing it to the handlers.
            """
            return record

        def handle(self, record):
            """
            Handle a record.

            This just loops through the handlers offering them the record
            to handle.
            """
            record = self.prepare(record)
            for handler in self.handlers:
                handler.handle(record)

        def _monitor(self):
            """
            Monitor the queue for records, and ask the handler
            to deal with them.

            This method runs on a separate, internal thread.
            The thread will terminate if it sees a sentinel object in the queue.
            """
            q = self.queue
            has_task_done = hasattr(q, 'task_done')
            while not self._stop.isSet():
                try:
                    record = self.dequeue(True)
                    if record is self._sentinel:
                        break
                    self.handle(record)
                    if has_task_done:
                        q.task_done()
                except queue.Empty:
                    pass
            # There might still be records in the queue.
            while True:
                try:
                    record = self.dequeue(False)
                    if record is self._sentinel:
                        break
                    self.handle(record)
                    if has_task_done:
                        q.task_done()
                except queue.Empty:
                    break

        def enqueue_sentinel(self):
            """
            This is used to enqueue the sentinel record.

            The base implementation uses put_nowait. You may want to override this
            method if you want to use timeouts or work with custom queue
            implementations.
            """
            self.queue.put_nowait(self._sentinel)

        def stop(self):
            """
            Stop the listener.

            This asks the thread to terminate, and then waits for it to do so.
            Note that if you don't call this before your application exits, there
            may be some records still left on the queue, which won't be processed.
            """
            self._stop.set()
            self.enqueue_sentinel()
            self._thread.join()
            self._thread = None

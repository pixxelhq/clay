import asyncio
import json
import sys
import threading
import time
from enum import Enum
from typing import Any, Callable, Dict, Union

import pika
import pika.adapters.blocking_connection
import pika.spec
import uvloop

from ramen.logger import RamenLogger
from ramen.models import ModelRequestsEvent, ModelResultsEvent


class RabbitModelRunner(object):

    _DEFAULT_EXCHANGE_NAME: str = "model_activity"
    _DEFAULT_EXCHANGE_TYPE: str = "topic"

    def __init__(
        self,
        model_name: str,
        model: Callable,
        model_args: Dict[str, Any],
        rabbitmq_host: str,
        rabbitmq_port: int,
        rabbitmq_qos: int,
        rabbitmq_durable: bool = False,
        enable_ramen_logger: bool = True,
        uvloop_policy: bool = True,
        consumer_callback: Union[Callable, None] = None,
        retries: int = 0,
    ) -> None:
        self._model = model
        self._model_args = model_args
        self._model_name = model_name
        self._retries = retries
        self._rabbitmq_host = rabbitmq_host
        self._rabbitmq_port = rabbitmq_port
        self._rabbitmq_qos = rabbitmq_qos
        self._rabbitmq_durable = rabbitmq_durable
        self._requests_binding_key = f"{self._model_name}.requests"
        self._results_binding_key = f"{self._model_name}.results"

        self.queue_names = self._get_queue_names()
        self.event_loop_policy = (
            uvloop.EventLoopPolicy()
            if uvloop_policy
            else asyncio.DefaultEventLoopPolicy()
        )
        if enable_ramen_logger:
            self._logger = RamenLogger("rmq_logger", False).add_console_handler()

    def _init_model(self) -> None:
        self._logger.info("Starting model initialization...")
        self._model = self._model(**self._model_args)
        self._logger.info("Model instantantiated...")

    def _run_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._logger.info("Starting model inference event loop")
        asyncio.set_event_loop(loop)
        loop.run_forever()
        self._logger.info("Event loop stopped")

    def _init_model_inference_event_loop(self) -> None:
        self._logger.info("Starting model inference event loop ...")
        asyncio.set_event_loop_policy(self.event_loop_policy)
        self._loop = asyncio.get_event_loop()
        self._t = threading.Thread(
            name="model_runner_event_thread",
            target=self._run_event_loop,
            args=(self._loop,),
            daemon=True,
        )
        self._t.start()
        self._logger.info("Started model inference event loop.")

    def _connect_to_rabbimq(self) -> None:
        self._logger.info("Connecting to rabbitmq broker ...")
        self._conn = pika.BlockingConnection(
            pika.ConnectionParameters(host=self._rabbitmq_host, port=self._rabbitmq_port)
        )
        self._logger.info("Connected to rabbitmq broker.")

    def _open_requests_channel(self) -> None:
        self._logger.info("Starting `requests` channel ...")
        self._requests_channel = self._conn.channel()
        self._logger.info("Started requests channel.")

    def _close_requests_channel(self) -> None:
        if self._requests_channel.is_open:
            self._requests_channel.close()
            self._logger.info("Closed requests channel.")

    def _open_results_channel(self) -> None:
        self._logger.info("Starting `results` channel...")
        self._results_channel = self._conn.channel()
        self._logger.info("Started results channel.")

    def _close_results_channel(self) -> None:
        if self._results_channel.is_open:
            self._results_channel.close()
            self._logger.info("Closed results chanel.")

    def _set_channel_qos(self) -> None:
        self._logger.info("Setting qos")
        self._requests_channel.basic_qos(prefetch_count=self._rabbitmq_qos)
        self._results_channel.basic_qos(prefetch_count=self._rabbitmq_qos)
        self._logger.info("qos set for the channels.")

    def _declare_exchange(self) -> None:
        self._logger.info("Started to declare exchange ...")
        self._requests_channel.exchange_declare(
            exchange=RabbitModelRunner._DEFAULT_EXCHANGE_NAME,
            exchange_type=RabbitModelRunner._DEFAULT_EXCHANGE_TYPE,
        )
        self._results_channel.exchange_declare(
            exchange=RabbitModelRunner._DEFAULT_EXCHANGE_NAME,
            exchange_type=RabbitModelRunner._DEFAULT_EXCHANGE_TYPE,
        )
        self._logger.info("Exchange declared.")

    def _declare_requests_queue(self, queue_name: str) -> None:
        self._logger.info("Attempting to declare requests queue ...")
        self._requests_queue = self._requests_channel.queue_declare(
            queue=queue_name, durable=self._rabbitmq_durable
        )
        self._logger.info(f"Declared requests queue. {self._requests_queue}")

    def _declare_results_queue(self, queue_name: str) -> None:
        self._logger.info("Attempting to declare results queue...")
        self._results_queue = self._results_channel.queue_declare(
            queue=queue_name, durable=self._rabbitmq_durable
        )
        self._logger.info("results queue declared.")

    def _bind_requests_queue(self, binding_key: str) -> None:
        self._logger.info("Attempting to bind requests queue")
        self._requests_channel.queue_bind(
            queue=self.queue_names.request.value,  # ignore
            exchange=RabbitModelRunner._DEFAULT_EXCHANGE_NAME,
            routing_key=self._requests_binding_key,
        )
        self._logger.info("requests queue boubd.")

    def _bind_results_queue(self, binding_key: str) -> None:
        self._logger.info("Attempting to bind results queue...")
        self._results_channel.queue_bind(
            queue=self.queue_names.result.value,  # ignore
            exchange=RabbitModelRunner._DEFAULT_EXCHANGE_NAME,
            routing_key=self._results_binding_key,
        )
        self._logger.info("Bound results queue.")

    def _get_queue_names(self) -> Enum:
        request_queue = f"queue_{self._model_name}_requests"
        results_queue = f"queue_{self._model_name}_results"
        return Enum("queues", {"request": request_queue, "result": results_queue})

    def _default_model_inference_callback(
        self,
        channel: pika.adapters.blocking_connection.BlockingChannel,
        method: pika.spec.Basic.Deliver,
        props: Any,
        body: Any,
    ) -> None:

        time_of_arrival = time.time()
        try:
            request: ModelRequestsEvent = ModelRequestsEvent(**json.loads(body.decode()))
        except Exception as err:
            self._logger.error(
                f"Error in parsing {method.delivery_tag}: {err}", exc_info=True
            )
            self._requests_channel.basic_reject(method.delivery_tag, requeue=False)
            self._logger.info(f"Msg {method.delivery_tag} is nacked.")
            return

        inference_id = request.inference_id
        delivery_tag = method.delivery_tag
        self._logger.info
        (
            "Starting Inference for: "
            f"Inference id: {inference_id}, delivery tag: {delivery_tag}"
        )

        inf_start_time = time.time()
        try:
            res = asyncio.run_coroutine_threadsafe(
                self._model.infer(request.inference_parameters), self._loop
            )
            res.result()
            status_code = 200
        except Exception as err:
            self._logger.error(
                f"Err in processing: Del-Tag: {delivery_tag} / Inf-ID: {inference_id}:"
                f"{err}",
            )
            res = str(err)  # type: ignore
            status_code = 500
        inf_end_time = time.time()

        message = ModelResultsEvent(
            emitter=self._model_name,
            model_name=self._model_name,
            inference_id=inference_id,
            model_recv_time=str(time_of_arrival),
            model_inf_start_time=str(inf_start_time),
            model_inf_end_time=str(inf_end_time),
            results=res,
            model_send_time=str(time.time()),
            status_code=status_code,
        )

        # moment to commit to queue and ack
        try:
            msg_properties = pika.spec.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent.value,
            )
            self._results_channel.basic_publish(
                exchange=RabbitModelRunner._DEFAULT_EXCHANGE_NAME,
                routing_key=self._results_binding_key,
                body=json.dumps(message.json()),
                properties=msg_properties,
            )
            self._requests_channel.basic_ack(delivery_tag=delivery_tag)
        except Exception as err:
            self._logger.error(f"Error in publishing response: {err}")
            if self._retries == 0:
                self._requests_channel.basic_nack(delivery_tag=delivery_tag)

    def start(self) -> None:
        self._logger.info("Starting model runner....")
        try:
            self._init_model()
            self._init_model_inference_event_loop()
            self._connect_to_rabbimq()
            self._open_requests_channel()
            self._open_results_channel()
            self._set_channel_qos()
            self._declare_requests_queue(queue_name=self.queue_names.request.value)
            self._declare_results_queue(queue_name=self.queue_names.result.value)
            self._declare_exchange()
            self._bind_requests_queue(binding_key=self._requests_binding_key)
            self._bind_results_queue(binding_key=self._results_binding_key)
            self._logger.info("Model runner is setup.")
        except Exception as err:
            self._logger.error(f"Setup Failed: {err}", exc_info=True)
            sys.exit(1)
        self._requests_channel.basic_consume(
            queue=self._requests_queue.method.queue,
            on_message_callback=self._default_model_inference_callback,
            auto_ack=False,
        )
        self._logger.info("Requests channel has started consuming...")
        try:
            self._requests_channel.start_consuming()
        except KeyboardInterrupt:
            self._logger.info("SIGTERM detected: Closing all connections.")
            self._requests_channel.close()
            self._results_channel.close()
            self._conn.close()

        # kills the event thread
        return

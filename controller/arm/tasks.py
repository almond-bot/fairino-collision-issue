import asyncio
from asyncio import StreamReader, StreamWriter

from controller.arm import shared
from core import utils
from lib.fairino.robot import RPC, RobotStatePkg

logger = utils.create_logger(__name__)


async def run_arm_status():
    reader: StreamReader | None = None
    writer: StreamWriter | None = None

    async def _get_stream_connection():
        if reader is None:
            new_reader, new_writer = await asyncio.open_connection(
                shared.ARM_IP, shared.ARM_PORT
            )
            return new_reader, new_writer
        else:
            return reader, writer

    while True:
        try:
            # Make sure the arm is there before we try to connect
            while not shared.is_connected():
                logger.warning("Arm not connected, trying to reconnect")
                await asyncio.to_thread(shared.connect)

                if not shared.is_connected():
                    # Wait to make sure we're not connecting aggressively
                    logger.info(
                        f"Arm not connected after reconnect attempt, waiting 10 seconds to reconnect"
                    )
                    await asyncio.sleep(10)

            try:
                reader, writer = await _get_stream_connection()
            except Exception as e:
                logger.warning(f"unable to open arm status stream: {e}")
                await asyncio.to_thread(shared.disconnect)
                continue

            recvbuf = bytearray(RPC.BUFFER_SIZE)
            tmp_recvbuf = bytearray(RPC.BUFFER_SIZE)
            state_pkg = bytearray(RPC.BUFFER_SIZE)
            find_head_flag = False
            index = 0
            length = 0
            tmp_len = 0

            data = await asyncio.wait_for(reader.read(RPC.BUFFER_SIZE), timeout=0.25)
            recvbuf[: len(data)] = data
            recvbyte = len(data)

            if recvbyte <= 0:
                # Reset the loop so we can try to reconnect
                if not shared.is_connected():
                    continue

                logger.warning(
                    "Failed to receive robot state bytes, trying to reconnect..."
                )

                shared.set_arm_status(None)
                writer.close()
                writer = None
                reader = None

                continue

            if tmp_len > 0:
                if tmp_len + recvbyte <= RPC.BUFFER_SIZE:
                    recvbuf = tmp_recvbuf[:tmp_len] + recvbuf[:recvbyte]
                    recvbyte += tmp_len
                    tmp_len = 0
                else:
                    tmp_len = 0

            for i in range(recvbyte):
                if recvbuf[i] == 0x5A and not find_head_flag:
                    if i + 4 < recvbyte:
                        if recvbuf[i + 1] == 0x5A:
                            find_head_flag = True
                            state_pkg[0] = recvbuf[i]
                            index += 1
                            length = length | recvbuf[i + 4]
                            length = length << 8
                            length = length | recvbuf[i + 3]
                        else:
                            continue
                    else:
                        tmp_recvbuf[: recvbyte - i] = recvbuf[i:recvbyte]
                        tmp_len = recvbyte - i
                        break
                elif find_head_flag and index < length + 5:
                    state_pkg[index] = recvbuf[i]
                    index += 1
                elif find_head_flag and index >= length + 5:
                    if i + 1 < recvbyte:
                        checksum = sum(state_pkg[:index])
                        checkdata = 0
                        checkdata = checkdata | recvbuf[i + 1]
                        checkdata = checkdata << 8
                        checkdata = checkdata | recvbuf[i]

                        if checksum == checkdata:
                            shared.set_arm_status(
                                RobotStatePkg.from_buffer_copy(recvbuf)
                            )
                        else:
                            find_head_flag = False
                            index = 0
                            length = 0
                            i += 1
                    else:
                        tmp_recvbuf[: recvbyte - i] = recvbuf[i:recvbyte]
                        tmp_len = recvbyte - i
                        break

        except Exception as e:
            if isinstance(e, asyncio.TimeoutError):
                logger.warning(f"arm status task error: {e}")
            else:
                logger.exception(f"arm status task error: {e}")

            shared.set_arm_status(None)
            writer.close()
            writer = None
            reader = None

            continue

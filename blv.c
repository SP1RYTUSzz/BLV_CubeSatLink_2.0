#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/spi.h"
#include "hardware/gpio.h"

#define BUF_LEN         0x100
#define FIFO_LEN        32

void printbuf(uint8_t buf[], size_t len) {
    int i;
    for (i = 0; i < len; ++i) {
        if (i % 16 == 15)
            printf("%02x\n", buf[i]);
        else
            printf("%02x ", buf[i]);
    }

    // append trailing newline if there isn't one
    if (i % 16) {
        putchar('\n');
    }
}

int main() {
    // Enable UART so we can print
    stdio_init_all();
#if !defined(spi_default) || !defined(PICO_DEFAULT_SPI_SCK_PIN) || !defined(PICO_DEFAULT_SPI_TX_PIN) || !defined(PICO_DEFAULT_SPI_RX_PIN) || !defined(PICO_DEFAULT_SPI_CSN_PIN)
#warning spi/spi_slave example requires a board with SPI pins
    puts("Default SPI pins were not defined");
#else
    // Enable SPI 0 at 1 MHz and connect to GPIOs
    // Enable UART0 at 9600 baud @ GP12, GP13
    // Enable UART1 at 9600 baud @ GP4, GP5
    {
    spi_init(spi_default, 1000 * 1000);
    spi_set_slave(spi_default, true);
    gpio_set_function(PICO_DEFAULT_SPI_RX_PIN, GPIO_FUNC_SPI);
    gpio_set_function(PICO_DEFAULT_SPI_SCK_PIN, GPIO_FUNC_SPI);
    gpio_set_function(PICO_DEFAULT_SPI_TX_PIN, GPIO_FUNC_SPI);
    gpio_set_function(PICO_DEFAULT_SPI_CSN_PIN, GPIO_FUNC_SPI);
    uart_init(uart0, 9600);
    gpio_set_function(12, GPIO_FUNC_UART);
    gpio_set_function(13, GPIO_FUNC_UART);
    uart_init(uart1, 9600);
    gpio_set_function(4, GPIO_FUNC_UART);
    gpio_set_function(5, GPIO_FUNC_UART);
    uart_set_format(uart0, 8, 1, UART_PARITY_NONE);
    uart_set_format(uart1, 8, 1, UART_PARITY_NONE);
    }

    uint8_t UART_tx_String0[] = "BBBBBBBBBBBBBBBBBBB\n";
    uint8_t UART_tx_String1[] = "This is a test message from Pico\n";
    uint8_t SPI_send_buf[1], SPI_receive_buf[1];          //CHANGE: this was BUF_LEN
    
    //indices
    int UART0wIndex = 0;             //this index is for UART0 write a single character at a time
    int UART1wIndex = 0;             //this index is for UART1 write a single character at a time
    int SPI_read_index = 0;
    

    while (true) {
        if (uart_is_writable(uart1)) {
            uart_putc(uart1, UART_tx_String1[UART1wIndex++]);         //Go through the message, send one byte at a time
            if (UART1wIndex >= strlen(UART_tx_String1)) {
                UART1wIndex = 0;
            }
        }
        if (uart_is_readable(uart1)) {              //read char from UART RX
            uart_read_blocking(uart1, SPI_send_buf, 1);
            spi_write_read_blocking(spi_default, SPI_send_buf, SPI_receive_buf, 1);
            
            //whatever just tryna print it
            if (SPI_receive_buf[0] != '\n') {
                UART_tx_String0[SPI_read_index++] = SPI_receive_buf[0];
            } else {
                SPI_read_index = 0;
            }
        }

        /*
        //duplication for UART2 (WIP)
        if (uart_is_writable(uart0)) {
            uart_putc(uart0, SendData0[UART1wIndex++]);
            if (UART0wIndex >= strlen(SendData0)) {
                UART0wIndex = 0;
            }
        }
        if (uart_is_readable(uart0)) {              //read char from UART RX
            uart_read_blocking(uart0, buf, 1);
            if (true) {
                spi_write_read_blocking(spi_default, buf, in_buf, 1);
            }
        }
        */
    }
#endif
}

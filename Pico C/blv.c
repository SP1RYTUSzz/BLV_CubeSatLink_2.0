/*
Dual UART-SPI
Originally created by Tri Do
*/
//#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/spi.h"
#include "hardware/gpio.h"

#define BUF_LEN         255
#define TIMEOUT         2000000
#define INTERCHAR       20000

int main() {
    // Enable UART so we can print
    // stdio_init_all();
#if !defined(spi_default) || !defined(PICO_DEFAULT_SPI_SCK_PIN) || !defined(PICO_DEFAULT_SPI_TX_PIN) || !defined(PICO_DEFAULT_SPI_RX_PIN) || !defined(PICO_DEFAULT_SPI_CSN_PIN)
#warning spi/spi_slave example requires a board with SPI pins
    puts("Default SPI pins were not defined");
#else
    {
    // Enable SPI 0 at 1 MHz and connect to GPIOs
    // Enable UART0 at 9600 baud @ GP12, GP13
    // Enable UART1 at 9600 baud @ GP4, GP5
    spi_init(spi_default, 1000 * 1000);
    spi_set_slave(spi_default, true);
    gpio_set_function(PICO_DEFAULT_SPI_RX_PIN, GPIO_FUNC_SPI);
    gpio_set_function(PICO_DEFAULT_SPI_SCK_PIN, GPIO_FUNC_SPI);
    gpio_set_function(PICO_DEFAULT_SPI_TX_PIN, GPIO_FUNC_SPI);
    gpio_set_function(PICO_DEFAULT_SPI_CSN_PIN, GPIO_FUNC_SPI);
    uart_init(uart0, 9600);
    uart_init(uart1, 9600);
    gpio_set_function(8, GPIO_FUNC_UART);
    gpio_set_function(9, GPIO_FUNC_UART);
    gpio_set_function(12, GPIO_FUNC_UART);
    gpio_set_function(13, GPIO_FUNC_UART);
    uart_set_format(uart0, 8, 1, UART_PARITY_NONE);
    uart_set_format(uart1, 8, 1, UART_PARITY_NONE);
    }

    uint8_t Tx_channel[1], Rx_channel[1];
    uint8_t UART0_rx_char[1],  UART1_rx_char[1],  UART0_tx_char[1],  UART1_tx_char[1];
    uint8_t UART0_rx_string[BUF_LEN], UART1_rx_string[BUF_LEN];
    uint8_t SPI0_send_string[BUF_LEN], SPI1_send_string[BUF_LEN];
    uint8_t SPI0_send_char[1], SPI1_send_char[1];
    int UART0_rx_index = 0, UART1_rx_index = 0;
    int SPI0_index = 0, SPI1_index = 0;

    Tx_channel[0] = '`';
    UART0_rx_char[0] = 'n';
    UART1_rx_char[0] = 'm';
    while (true) {
        //CALCULATING SPI SEND
        if (SPI0_send_string != NULL && SPI0_index < strlen(SPI0_send_string)) {
            *SPI0_send_char = SPI0_send_string[SPI0_index];
            if (*SPI0_send_char == '\n') {
                strcpy(SPI0_send_string, "");
                SPI0_index = -1;
            }
            SPI0_index++;
        } else {
            *SPI0_send_char = '\0';
        }
        if (SPI1_send_string != NULL && SPI1_index < strlen(SPI1_send_string)) {
            *SPI1_send_char = SPI1_send_string[SPI1_index];
            if (*SPI1_send_char == '\n') {
                strcpy(SPI1_send_string, "");
                SPI1_index = -1;
            }
            SPI1_index++;
        } else {
            *SPI1_send_char = '\0';
        }
        //NOW SEND THE SPI SEQUENCE
        uint8_t SPI_send_sequence[3];
        uint8_t SPI_receive_sequence[3];
        SPI_send_sequence[0] = Tx_channel[0];
        SPI_send_sequence[1] = SPI0_send_char[0];
        SPI_send_sequence[2] = SPI1_send_char[0];
        spi_write_read_blocking(spi_default, SPI_send_sequence, SPI_receive_sequence, 3);
        Rx_channel[0] = SPI_receive_sequence[0];
        UART0_tx_char[0] = SPI_receive_sequence[1];
        UART1_tx_char[0] = SPI_receive_sequence[2];

        //UART DOWN BELOW
        //WRITE TO UART WITH NO BUFFER ON OUR END?
        if (uart_is_writable(uart0)) {
            uart_putc(uart0, UART0_tx_char[0]);
        }
        if (uart_is_writable(uart1)) {
            uart_putc(uart1, UART1_tx_char[0]);
        }
        //READ FROM UART THEN ADD TO UART_RX_STRING THEN PUT TO SPI_SEND_STRING WHEN FULL
        while (uart_is_readable(uart0)) {
            uart_read_blocking(uart0, UART0_rx_char, 1);
            UART0_rx_string[UART0_rx_index++] = *UART0_rx_char;
            if (*UART0_rx_char == '\n' || *UART0_rx_char == '}' || UART0_rx_index >= BUF_LEN) { //this need to be fixed bruh
                UART0_rx_index = 0;
                for (int i = 0; i < BUF_LEN; i++) {
                    SPI0_send_string[i] = UART0_rx_string[i];
                }
            }
        }
        /*
        if (t0-time_us_64() > TIMEOUT) {
            timeout_sent0 = true;
            UART0_rx_string[UART0_rx_index+1] = '\n';
            UART0_rx_index = 0;
            for (int i = 0; i < BUF_LEN; i++) {
                SPI0_send_string[i] = UART0_rx_string[i];
            }
        }
        */
        while (uart_is_readable(uart1)) {
            uart_read_blocking(uart1, UART1_rx_char, 1);
            UART1_rx_string[UART1_rx_index++] = *UART1_rx_char;
            if (*UART1_rx_char == '\n'|| *UART1_rx_char == '}' || UART1_rx_index >= BUF_LEN) {
                UART1_rx_index = 0;
                for (int i = 0; i < BUF_LEN; i++) {
                    SPI1_send_string[i] = UART1_rx_string[i];
                }
            }
        }
        /*
        if (t1-time_us_64() > TIMEOUT) {
            timeout_sent1 = true;
            UART1_rx_string[UART1_rx_index+1] = '\n';
            UART1_rx_index = 0;
            for (int i = 0; i < BUF_LEN; i++) {
                SPI1_send_string[i] = UART1_rx_string[i];
            }
        }
        */
    }
#endif
}

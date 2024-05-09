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

#define BUF_LEN         0x100
/*
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
*/

int main() {
    // Enable UART so we can print
    // stdio_init_all();
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
/*
    uint8_t UART_tx_String0[255] = "BBBBBBBBBBBBBBBBBBB\n";
    uint8_t UART_tx_String1[255] = "";
    uint8_t SPI_send_buf[1], SPI_receive_buf[1];          //CHANGE: this was BUF_LEN
    uint8_t UART_tx_channel[1] = "`";     //select which uart to send message to (per char) (` is internal, # is 1, $ is 2)
    uint8_t UART_rx_channel[1] = "#";
    //indices
    int UART0wIndex = 0;             //this index is for UART0 write a single character at a time
    int UART1wIndex = 0;             //this index is for UART1 write a single character at a time
    int SPI_read_index = 0;
*/

    uint8_t Tx_channel[1], Rx_channel[1];
    uint8_t UART0_rx_char[1],  UART1_rx_char[1],  UART0_tx_char[1],  UART1_tx_char[1];
    uint8_t UART0_rx_string[255], UART1_rx_string[255];
    uint8_t SPI0_send_string[255], SPI1_send_string[255];
    uint8_t SPI0_send_char[1], SPI1_send_char[1];

    int UART0_rx_index = 0, UART1_rx_index = 0;
    int SPI0_index = 0, SPI1_index = 0;

    Tx_channel[0] = '`';
    UART0_rx_char[0] = 'n';
    UART1_rx_char[0] = 'm';
    while (true) {
        if (SPI0_send_string != NULL && SPI0_index < strlen(SPI0_send_string)) {
            *SPI0_send_char = SPI0_send_string[SPI0_index];
            if (*SPI0_send_char == '\n') {
                strcpy(SPI0_send_string, "");
                SPI0_index = 0;
            }
            SPI0_index++;
        } else {
            *SPI0_send_char = '\0';
        }
        if (SPI1_send_string != NULL && SPI1_index < strlen(SPI1_send_string)) {
            *SPI1_send_char = SPI1_send_string[SPI1_index];
            if (*SPI1_send_char == '\n') {
                strcpy(SPI1_send_string, "");
                SPI1_index = 0;
            }
            SPI1_index++;
        } else {
            *SPI1_send_char = '\0';
        }
        spi_write_read_blocking(spi_default, Tx_channel, Rx_channel, 1);
        spi_write_read_blocking(spi_default, SPI0_send_char, UART1_tx_char, 1);
        spi_write_read_blocking(spi_default, SPI1_send_char, UART0_tx_char, 1); //flipped cus UART rx is SPI tx

        if (uart_is_writable(uart0)) {
            uart_putc(uart0, UART0_tx_char[0]);
        }
        if (uart_is_writable(uart1)) {
            uart_putc(uart1, UART1_tx_char[0]);
        }
        while (uart_is_readable(uart0)) {
            uart_read_blocking(uart0, UART0_rx_char, 1);
            UART0_rx_string[UART0_rx_index++] = *UART0_rx_char;
            if (UART0_rx_index >= 255) {
                UART0_rx_index = 0;
                *UART0_rx_char = '\n';
            }
            if (*UART0_rx_char == '\n') {
                UART0_rx_index = 0;
                for (int i = 0; i < 255; i++) {
                    SPI0_send_string[i] = UART0_rx_string[i];
                }
            }
        }
        while (uart_is_readable(uart1)) {
            uart_read_blocking(uart1, UART1_rx_char, 1);
            UART1_rx_string[UART1_rx_index++] = *UART1_rx_char;
            if (UART1_rx_index >= 255) {
                UART1_rx_index = 0;
                *UART1_rx_char = '\n';
            }
            if (*UART1_rx_char == '\n') {
                UART1_rx_index = 0;
                for (int i = 0; i < 255; i++) {
                    SPI1_send_string[i] = UART1_rx_string[i];
                }
            }
        }
    }

/*
    //new variables declare
    uint8_t Tx_channel[1], Rx_channel[1];
    uint8_t SPI_tx_char[1], SPI_rx_char[1];
    uint8_t UART0_rx_char[1], UART1_rx_char[1];
    uint8_t UART0_tx_string[255], UART1_tx_string[255];
    uint8_t UART0_rx_string[255], UART1_rx_string[255];

    int SPI0_read_index = 0, SPI1_read_index = 0;
    int SPI0_write_index = 0, SPI1_write_index = 0;
    int UART0_tx_index = 0, UART1_tx_index = 0;
    int UART0_rx_index = 0, UART1_rx_index = 0;
    bool UART0_send_flag = false, UART1_send_flag = false;


    SPI_tx_char[0] = 'k';
    spi_write_read_blocking(spi_default, Tx_channel, Rx_channel, 1);  //not sure about the order
    spi_write_read_blocking(spi_default, SPI_tx_char, SPI_rx_char, 1);
    if (Tx_channel[0] == '#') {
        UART0_tx_string[SPI0_read_index++] = SPI_rx_char[0];
        if (SPI0_read_index >= 255) { SPI0_read_index = 0; }
    } else if (Tx_channel[0] == '$') {
        UART1_tx_string[SPI1_read_index++] = SPI_rx_char[0];
        if (SPI1_read_index >= 255) { SPI1_read_index = 0; }
    }
    while (true) {
        if (uart_is_writable(uart1)) {
            uart_putc(uart1, UART1_tx_string[UART1_tx_index++]);
            if (UART1_tx_index >= 255) {
                UART1_tx_index = 0;
            }
        }
        if (uart_is_readable(uart1)) {
            UART1_send_flag = true;
            uart_read_blocking(uart1, UART1_rx_char, 1);
            UART1_rx_string[UART1_rx_index] = UART1_rx_char[0];
            if (UART1_rx_index >= 255) {
                UART1_rx_index = 0;
            }
        }
        if (UART1_send_flag) {
            Tx_channel[0] = '$';
            SPI_tx_char[0] = UART1_rx_string[SPI1_write_index++];
            if (SPI1_write_index >= 255) { SPI1_write_index = 0; }
            UART1_send_flag = false;

            spi_write_read_blocking(spi_default, Tx_channel, Rx_channel, 1);  
            spi_write_read_blocking(spi_default, SPI_tx_char, SPI_rx_char, 1);
            if (Rx_channel[0] == '#') {
                UART0_tx_string[SPI0_read_index++] = SPI_rx_char[0];
                if (SPI0_read_index >= 255) { SPI0_read_index = 0; }
            } else if (Rx_channel[0] == '$') {
                UART1_tx_string[SPI1_read_index++] = SPI_rx_char[0];
                if (SPI1_read_index >= 255) { SPI1_read_index = 0; }
            }
        }
    }
*/        

/*
        if (uart_is_writable(uart1)) {
            uart_putc(uart1, UART_tx_String1[UART1wIndex++]);         //Go through the message, send one byte at a time
            if (UART1wIndex >= strlen(UART_tx_String1)) {
                UART1wIndex = 0;
            }
        }
        if (uart_is_readable(uart1)) {              //read char from UART RX
            uart_read_blocking(uart1, SPI_send_buf, 1);
            spi_write_read_blocking(spi_default, UART_rx_channel, UART_tx_channel, 1);  //not sure about the order
            spi_write_read_blocking(spi_default, SPI_send_buf, SPI_receive_buf, 1);
            
            //Print if '\n' is detected
            if (SPI_receive_buf[0] != '\n') {
                UART_tx_String1[SPI_read_index++] = SPI_receive_buf[0];
            } else {
                SPI_read_index = 0;
            }
        }
*/
#endif
}

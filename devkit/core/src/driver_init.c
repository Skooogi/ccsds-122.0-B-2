/*
 * Code generated from Atmel Start.
 *
 * This file will be overwritten when reconfiguring your Atmel Start project.
 * Please copy examples or other code you want to keep to a separate file
 * to avoid losing it when reconfiguring.
 */

#include "driver_init.h"
#include <hal_init.h>
#include <hpl_pmc.h>
#include <peripheral_clk_config.h>
#include <utils.h>
#include <hpl_usart_base.h>

/*! The buffer size for USART */
#define EDBG_COM_BUFFER_SIZE 256

struct usart_async_descriptor EDBG_COM;

static uint8_t EDBG_COM_buffer[EDBG_COM_BUFFER_SIZE];

/**
 * \brief USART Clock initialization function
 *
 * Enables register interface and peripheral clock
 */
void EDBG_COM_CLOCK_init()
{
	_pmc_enable_periph_clock(ID_USART1);
}

/**
 * \brief USART pinmux initialization function
 *
 * Set each required pin to USART functionality
 */
void EDBG_COM_PORT_init()
{

	gpio_set_pin_function(EDBG_COM_RX, MUX_PA21A_USART1_RXD1);

	gpio_set_pin_function(EDBG_COM_TX, MUX_PB4D_USART1_TXD1);
}

/**
 * \brief USART initialization function
 *
 * Enables USART peripheral, clocks and initializes USART driver
 */
void EDBG_COM_init(void)
{
	EDBG_COM_CLOCK_init();
	EDBG_COM_PORT_init();
	usart_async_init(&EDBG_COM, USART1, EDBG_COM_buffer, EDBG_COM_BUFFER_SIZE, _usart_get_usart_async());
}

void system_init(void)
{
	init_mcu();

	_pmc_enable_periph_clock(ID_PIOA);

	/* Disable Watchdog */
	hri_wdt_set_MR_WDDIS_bit(WDT);

	/* GPIO on PA23 */

	gpio_set_pin_level(LED0,
	                   // <y> Initial level
	                   // <id> pad_initial_level
	                   // <false"> Low
	                   // <true"> High
	                   true);

	// Set pin direction to output
	gpio_set_pin_direction(LED0, GPIO_DIRECTION_OUT);

	gpio_set_pin_function(LED0, GPIO_PIN_FUNCTION_OFF);

	EDBG_COM_init();
}

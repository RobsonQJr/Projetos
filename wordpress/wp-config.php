<?php
/**
 * The base configuration for WordPress
 *
 * The wp-config.php creation script uses this file during the installation.
 * You don't have to use the website, you can copy this file to "wp-config.php"
 * and fill in the values.
 *
 * This file contains the following configurations:
 *
 * * Database settings
 * * Secret keys
 * * Database table prefix
 * * ABSPATH
 *
 * @link https://developer.wordpress.org/advanced-administration/wordpress/wp-config/
 *
 * @package WordPress
 */

// ** Database settings - You can get this info from your web host ** //
/** The name of the database for WordPress */
define( 'DB_NAME', 'robss enterprise' );

/** Database username */
define( 'DB_USER', 'root' );

/** Database password */
define( 'DB_PASSWORD', '' );

/** Database hostname */
define( 'DB_HOST', 'localhost' );

/** Database charset to use in creating database tables. */
define( 'DB_CHARSET', 'utf8mb4' );

/** The database collate type. Don't change this if in doubt. */
define( 'DB_COLLATE', '' );

/**#@+
 * Authentication unique keys and salts.
 *
 * Change these to different unique phrases! You can generate these using
 * the {@link https://api.wordpress.org/secret-key/1.1/salt/ WordPress.org secret-key service}.
 *
 * You can change these at any point in time to invalidate all existing cookies.
 * This will force all users to have to log in again.
 *
 * @since 2.6.0
 */
define( 'AUTH_KEY',         'jSKt}jNjhE>7$yh;!W@0%xz6eO9[~{y1++agt~5i/r03`D4|p,9dB[t4i%~pEu$%' );
define( 'SECURE_AUTH_KEY',  ':&ypeb;H--T>-?OY>;T5iJdYq6zwAC0Wsfrss &W}4V(XVk#,_gJ20usc@0vn>b#' );
define( 'LOGGED_IN_KEY',    'XPF3^<9hI+N0AsC9Ls}d3@GnuC%FtuitrFAZit5kOGton[{L@mpLNefR;^kaD;X-' );
define( 'NONCE_KEY',        '^l=tOc],M82!Mi6vmJ1Ty^:^st={hJ#L~R|= /D6A$Mu|To`mV7P|_dlN4kXR_a{' );
define( 'AUTH_SALT',        'd+EdO6P,t9iss:2$zpnb_j8#a:{A-qV >zt#b^QyhST8-R+S;O_I0Y(&JA~-K*)>' );
define( 'SECURE_AUTH_SALT', 'q+Ul_RQplmBZ/o:{j*%G|?H{wam4NWL4pF7aP2cuCcGSk(heXD#$8~oi,-6o^.3u' );
define( 'LOGGED_IN_SALT',   ' WHluvLg&lE{,b8!QU=8#=oBr0XT69 YImN&hyhiWy`#%cgK<RJ$-Igbo0;wY<X]' );
define( 'NONCE_SALT',       '3!)tCwJCskD%pGN]5D%CXXC4$CRq5D7j*spfGm%~FVHkx47m^@p|HcQo~ $%V kT' );

/**#@-*/

/**
 * WordPress database table prefix.
 *
 * You can have multiple installations in one database if you give each
 * a unique prefix. Only numbers, letters, and underscores please!
 *
 * At the installation time, database tables are created with the specified prefix.
 * Changing this value after WordPress is installed will make your site think
 * it has not been installed.
 *
 * @link https://developer.wordpress.org/advanced-administration/wordpress/wp-config/#table-prefix
 */
$table_prefix = 'wp_';

/**
 * For developers: WordPress debugging mode.
 *
 * Change this to true to enable the display of notices during development.
 * It is strongly recommended that plugin and theme developers use WP_DEBUG
 * in their development environments.
 *
 * For information on other constants that can be used for debugging,
 * visit the documentation.
 *
 * @link https://developer.wordpress.org/advanced-administration/debug/debug-wordpress/
 */
define( 'WP_DEBUG', false );

/* Add any custom values between this line and the "stop editing" line. */



/* That's all, stop editing! Happy publishing. */

/** Absolute path to the WordPress directory. */
if ( ! defined( 'ABSPATH' ) ) {
	define( 'ABSPATH', __DIR__ . '/' );
}

/** Sets up WordPress vars and included files. */
require_once ABSPATH . 'wp-settings.php';

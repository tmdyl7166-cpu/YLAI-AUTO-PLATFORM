import { createApp } from 'vue';
import { compileTemplate } from '@vue/compiler-dom';
import { renderToString } from '@vue/server-renderer';

global.Vue = { createApp };
global.VueCompilerDOM = { compileTemplate };
global.VueServerRenderer = { renderToString };
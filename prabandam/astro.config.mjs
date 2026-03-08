// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

// https://astro.build/config
export default defineConfig({
	markdown: {
		remarkPlugins: [remarkMath],
		rehypePlugins: [rehypeKatex],
	},
	integrations: [
		starlight({
			title: 'Prabandam',
			description: 'First-principles graph + tantra documentation',
			customCss: ['./src/styles/custom.css'],
			sidebar: [
				{
					label: 'Whitepaper',
					items: [
						{ label: 'Executive Summary', slug: 'whitepaper/executive-summary' },
						{ label: 'Input-Output Graph Math', slug: 'whitepaper/input-output-graph-math' },
						{ label: 'Learning Without Retraining', slug: 'whitepaper/learning-without-retraining' },
						{ label: 'Proof-Graph Running Examples', slug: 'whitepaper/proof-graph-running-examples' },
						{ label: 'System Overview', slug: 'tattva/system-overview' },
						{ label: 'First Principles Model', slug: 'tattva/first-principles-model' },
					],
				},
				{
					label: 'Prayoga',
					items: [
						{ label: 'Music + Code Generation', slug: 'prayoga/music-and-code-generation' },
					],
				},
				{
					label: 'Reference',
					items: [{ label: 'Equations', slug: 'reference/equations' }],
				},
			],
		}),
	],
});

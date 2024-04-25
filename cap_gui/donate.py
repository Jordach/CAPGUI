import gradio as gr

markdown = """
# Donation Goal:
Developing the next generation of generalist image generation models is expensive, and we need your help.

All funds raised across all channels will be used to fund infrastructure rental to bring you the best version of Resonance, 
and help cover costs associated with ensuring free public access to the model remains available to anyone who wishes to use it.

[Current Goal Link](https://www.zeffy.com/en-US/fundraising/ec77a176-672f-4aa9-ba4d-4c74607379fd)

# Donation Links:

## US Dollar:
[Ko-Fi](https://ko-fi.com/K3K2X1ALM)

## Worldwide Currencies:
[LiberaPay](https://liberapay.com/MeanOldTree/donate)
[PayPal](https://www.paypal.com/donate/?hosted_button_id=CUT8PU94A9H4A)
"""

def donate_tab(global_ctx, local_ctx):
	local_ctx["donate_window"] = gr.Markdown(markdown, line_breaks=True)
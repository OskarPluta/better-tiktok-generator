import os
from pathlib import Path
from PIL import Image
from transformers import AutoModelForImageSegmentation
import torch
from torchvision import transforms


# device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
def main():
    device = "cpu"
    birefnet = AutoModelForImageSegmentation.from_pretrained(
        'zhengpeng7/BiRefNet', 
        trust_remote_code=True
    )
    birefnet.to(device)
    birefnet.eval()

    transform_image = transforms.Compose([
        transforms.Resize((1024, 1024)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    def process_image(input_path, output_path):
        image = Image.open(input_path).convert('RGB')
        original_size = image.size
        input_images = transform_image(image).unsqueeze(0).to(device)
        with torch.no_grad():
            preds = birefnet(input_images)[-1].sigmoid().cpu()
        pred = preds[0].squeeze()
        pred_pil = transforms.ToPILImage()(pred)
        mask = pred_pil.resize(original_size)
        
        image = Image.open(input_path).convert('RGBA')
        image.putalpha(mask)
        
        image.save(output_path, 'PNG')
        print(f"Processed: {input_path} -> {output_path}")

    def process_directory(input_dir='data/characters', output_dir='data/characters_without_background'):
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        image_files = []
        for ext in image_extensions:
            image_files.extend(input_path.rglob(f'*{ext}'))
            image_files.extend(input_path.rglob(f'*{ext.upper()}'))
        
        print(f"Processing {len(image_files)} images")
        processed_count = 0
        skipped_count = 0
        
        for img_file in image_files:
            relative_path = img_file.relative_to(input_path)
            output_file = output_path / relative_path.with_suffix('.png')
            if output_file.exists():
                skipped_count += 1
                continue

            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                process_image(str(img_file), str(output_file))
                processed_count += 1
            except Exception as e:
                print(f"Error processing {img_file}: {e}")
        
        print(f"Processed: {processed_count} images")
        print(f"Skipped: {skipped_count} images")
    
    process_directory()

if __name__ == "__main__":
    main()

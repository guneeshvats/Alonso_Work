import os
import subprocess
import typer

app = typer.Typer()

@app.command()
def process_images(
    image_folder: str = typer.Argument(..., help="Folder containing the images."),
    unsan_file: str = typer.Argument(..., help="Path to the unsan file."),
    config_path: str = typer.Argument(..., help="Path to the config file."),
    output_dir: str = typer.Argument(..., help="Output directory for results.")
):
    """
    This function processes all images in the specified folder using the provided unsan_file, config_path, and output_dir.
    It also sets OMP_NUM_THREADS=1 and MKL_NUM_THREADS=1 for the subprocesses.
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif'}

    image_files = [f for f in os.listdir(image_folder) if os.path.splitext(f)[1].lower() in image_extensions]

    for image_file in image_files:
        image_path = os.path.join(image_folder, image_file)
        print(f"Processing {image_path}")
        
        env_vars = os.environ.copy()
        env_vars["OMP_NUM_THREADS"] = "1"
        env_vars["MKL_NUM_THREADS"] = "1"
        
        subprocess.run(
            ["python3", "yolo_page.py", image_path, unsan_file, config_path, output_dir],
            env=env_vars
        )

if __name__ == "__main__":
    app()


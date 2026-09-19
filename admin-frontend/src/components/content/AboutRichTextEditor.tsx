import Link from "@tiptap/extension-link";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import {
  Bold,
  Check,
  Italic,
  Link2,
  List,
  ListOrdered,
  Quote,
  Redo2,
  Strikethrough,
  Undo2,
  Unlink,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

interface AboutRichTextEditorProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

interface ToolbarButtonProps {
  label: string;
  active?: boolean;
  disabled?: boolean;
  onClick: () => void;
  children: React.ReactNode;
}

function ToolbarButton({
  label,
  active = false,
  disabled = false,
  onClick,
  children,
}: ToolbarButtonProps) {
  return (
    <button
      className={`about-rich-editor__button${
        active ? " about-rich-editor__button--active" : ""
      }`}
      type="button"
      aria-label={label}
      title={label}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

function normalizeLink(value: string): string {
  const trimmed = value.trim();

  if (!trimmed) {
    return "";
  }

  if (/^(https?:\/\/|mailto:)/i.test(trimmed)) {
    return trimmed;
  }

  if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
    return `mailto:${trimmed}`;
  }

  return `https://${trimmed}`;
}

export function AboutRichTextEditor({
  value,
  onChange,
  disabled = false,
}: AboutRichTextEditorProps) {
  const [isLinkEditorOpen, setIsLinkEditorOpen] = useState(false);
  const [linkValue, setLinkValue] = useState("");
  const linkInputRef = useRef<HTMLInputElement>(null);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: false,
        code: false,
        codeBlock: false,
        horizontalRule: false,
      }),
      Link.configure({
        openOnClick: false,
        autolink: true,
        defaultProtocol: "https",
        HTMLAttributes: {
          target: "_blank",
        },
      }),
    ],
    content: value,
    editable: !disabled,
    immediatelyRender: false,
    onUpdate: ({ editor: currentEditor }) => {
      onChange(currentEditor.getHTML());
    },
  });

  useEffect(() => {
    if (!editor) {
      return;
    }

    editor.setEditable(!disabled);
  }, [disabled, editor]);

  useEffect(() => {
    if (!editor) {
      return;
    }

    const current = editor.getHTML();

    if (current !== value) {
      editor.commands.setContent(value || "", { emitUpdate: false });
    }
  }, [editor, value]);

  useEffect(() => {
    if (!isLinkEditorOpen) {
      return;
    }

    const frame = window.requestAnimationFrame(() => {
      linkInputRef.current?.focus();
      linkInputRef.current?.select();
    });

    return () => window.cancelAnimationFrame(frame);
  }, [isLinkEditorOpen]);

  if (!editor) {
    return <div className="about-rich-editor about-rich-editor--loading" />;
  }

  function openLinkEditor() {
    if (!editor || disabled) {
      return;
    }

    const previousUrl = editor.getAttributes("link").href as string | undefined;

    setLinkValue(previousUrl ?? "");
    setIsLinkEditorOpen(true);
  }

  function closeLinkEditor() {
    setIsLinkEditorOpen(false);
    setLinkValue("");
    editor?.commands.focus();
  }

  function applyLink() {
    if (!editor) {
      return;
    }

    const normalized = normalizeLink(linkValue);

    if (!normalized) {
      editor.chain().focus().extendMarkRange("link").unsetLink().run();
      closeLinkEditor();
      return;
    }

    editor
      .chain()
      .focus()
      .extendMarkRange("link")
      .setLink({ href: normalized })
      .run();

    setIsLinkEditorOpen(false);
    setLinkValue("");
  }

  function removeLink() {
    if (!editor) {
      return;
    }

    editor.chain().focus().extendMarkRange("link").unsetLink().run();
    setIsLinkEditorOpen(false);
    setLinkValue("");
  }

  return (
    <div
      className={`about-rich-editor${
        disabled ? " about-rich-editor--disabled" : ""
      }`}
    >
      <div className="about-rich-editor__toolbar" aria-label="Text formatting">
        <div className="about-rich-editor__toolbar-group">
          <ToolbarButton
            label="Bold"
            active={editor.isActive("bold")}
            disabled={disabled}
            onClick={() => editor.chain().focus().toggleBold().run()}
          >
            <Bold size={17} />
          </ToolbarButton>

          <ToolbarButton
            label="Italic"
            active={editor.isActive("italic")}
            disabled={disabled}
            onClick={() => editor.chain().focus().toggleItalic().run()}
          >
            <Italic size={17} />
          </ToolbarButton>

          <ToolbarButton
            label="Strikethrough"
            active={editor.isActive("strike")}
            disabled={disabled}
            onClick={() => editor.chain().focus().toggleStrike().run()}
          >
            <Strikethrough size={17} />
          </ToolbarButton>
        </div>

        <span className="about-rich-editor__divider" />

        <div className="about-rich-editor__toolbar-group">
          <ToolbarButton
            label="Bullet list"
            active={editor.isActive("bulletList")}
            disabled={disabled}
            onClick={() => editor.chain().focus().toggleBulletList().run()}
          >
            <List size={17} />
          </ToolbarButton>

          <ToolbarButton
            label="Numbered list"
            active={editor.isActive("orderedList")}
            disabled={disabled}
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
          >
            <ListOrdered size={17} />
          </ToolbarButton>

          <ToolbarButton
            label="Blockquote"
            active={editor.isActive("blockquote")}
            disabled={disabled}
            onClick={() => editor.chain().focus().toggleBlockquote().run()}
          >
            <Quote size={17} />
          </ToolbarButton>
        </div>

        <span className="about-rich-editor__divider" />

        <div className="about-rich-editor__toolbar-group">
          <ToolbarButton
            label="Add or edit link"
            active={editor.isActive("link") || isLinkEditorOpen}
            disabled={disabled}
            onClick={openLinkEditor}
          >
            <Link2 size={17} />
          </ToolbarButton>

          <ToolbarButton
            label="Remove link"
            disabled={disabled || !editor.isActive("link")}
            onClick={removeLink}
          >
            <Unlink size={17} />
          </ToolbarButton>
        </div>

        <span className="about-rich-editor__toolbar-spacer" />

        <div className="about-rich-editor__toolbar-group">
          <ToolbarButton
            label="Undo"
            disabled={disabled || !editor.can().chain().focus().undo().run()}
            onClick={() => editor.chain().focus().undo().run()}
          >
            <Undo2 size={17} />
          </ToolbarButton>

          <ToolbarButton
            label="Redo"
            disabled={disabled || !editor.can().chain().focus().redo().run()}
            onClick={() => editor.chain().focus().redo().run()}
          >
            <Redo2 size={17} />
          </ToolbarButton>
        </div>
      </div>

      {isLinkEditorOpen ? (
        <form
          className="about-rich-editor__link-editor"
          onSubmit={(event) => {
            event.preventDefault();
            applyLink();
          }}
        >
          <div className="about-rich-editor__link-icon">
            <Link2 size={17} />
          </div>

          <label>
            <span>Link URL</span>
            <input
              ref={linkInputRef}
              type="text"
              inputMode="url"
              value={linkValue}
              placeholder="https://example.com"
              disabled={disabled}
              onChange={(event) => setLinkValue(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Escape") {
                  event.preventDefault();
                  closeLinkEditor();
                }
              }}
            />
          </label>

          <button
            className="about-rich-editor__link-action about-rich-editor__link-action--apply"
            type="submit"
            aria-label="Apply link"
            title="Apply link"
            disabled={disabled}
          >
            <Check size={17} />
          </button>

          <button
            className="about-rich-editor__link-action"
            type="button"
            aria-label="Cancel"
            title="Cancel"
            onClick={closeLinkEditor}
          >
            <X size={17} />
          </button>
        </form>
      ) : null}

      <EditorContent editor={editor} />
    </div>
  );
}
